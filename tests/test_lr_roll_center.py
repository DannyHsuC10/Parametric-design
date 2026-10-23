"""Physical checks for the LR model's equivalent RC body-spring branch."""

import unittest

import numpy as np
from scipy.integrate import solve_ivp

from analysis.suspension_models import batch_cases, batch_runner
from analysis.suspension_models.model import LR_model
from analysis.suspension_models.parameters import make_suspension, plugin_metadata


VEHICLE = {
    "ms": 280.0, "mu": 12.0, "Ks_roll_N_per_m": 24000.0,
    "Ks_pitch_N_per_m": 40000.0, "cog_total_Ixx_kg_m2": 64.0,
    "t": 1.4, "h_cog": 0.35, "hl_front_roll_center_m": 0.08,
    "hl_rear_roll_center_m": 0.16, "k_frame_to_roll_ratio": 10.0,
}


class LrRollCenterTests(unittest.TestCase):
    def simulate_step(self, suspension, dt, duration=0.15):
        suspension, state, _, model, config = batch_runner.prepare_case(
            "LR", "rollcenter_all", "cornering", dt=dt, suspension=suspension,
        )
        config["duration_s"] = duration

        def road(state):
            state.ay = -12.0

        return batch_runner.simulate_case(suspension, state, road, model, config).result()

    def test_equivalent_mass_tracks_half_car_sprung_mass_and_preserves_vehicle_mass(self):
        for values in ({}, VEHICLE, VEHICLE | {"ms": 560.0, "mu": 30.0}):
            with self.subTest(values=values):
                sus = make_suspension("LR", values)
                self.assertEqual(sus.m_frame, (2 * sus.ms) / 4)
                self.assertEqual(sus.m_corner, sus.ms + sus.mu)
                self.assertEqual(sus.k_frame / sus.k_roll, 10)
                self.assertEqual(sus.zeta_frame, 0.5)
                self.assertAlmostEqual(sus.c_frame / (2 * np.sqrt(sus.k_frame * sus.m_frame)), 0.5)
                self.assertFalse(hasattr(sus, "tau_rc"))

    def test_optional_frame_damping_is_exposed_only_for_the_compliant_model(self):
        metadata = plugin_metadata("half_rollcenter_all_model")
        self.assertIn("zeta_frame", metadata["VISIBLE_PARAMETERS"])
        self.assertEqual(metadata["PARAMETER_DEFAULTS"]["zeta_frame"], 0.5)
        self.assertNotIn("c_frame", metadata["PARAMETERS"])
        self.assertNotIn("zeta_frame", plugin_metadata("half_suspension_model_lr")["PARAMETERS"])
        for ratio in (0, 0.5, 1.0):
            sus = make_suspension("LR", VEHICLE | {"zeta_frame": ratio, "ms": 560, "k_frame_to_roll_ratio": 8})
            self.assertAlmostEqual(sus.c_frame / (2 * np.sqrt(sus.k_frame * sus.m_frame)), ratio)
        for damping in (-1, np.nan, np.inf):
            with self.subTest(damping=damping), self.assertRaises(ValueError):
                make_suspension("LR", VEHICLE | {"zeta_frame": damping})

    def test_initial_roll_moment_uses_sprung_mass_and_frame_force_starts_from_zero(self):
        for unsprung in (12.0, 30.0):
            sus = make_suspension("LR", VEHICLE | {"mu": unsprung})
            state = batch_cases.lr_state(0.001)
            state.ay = -12.0
            LR_model.Half_rollcenter_all_model(sus, state)
            expected_moment = state.ay * (2 * sus.ms) * (sus.h_cg - sus.h_rc)
            self.assertAlmostEqual(state.Mx, expected_moment)
            self.assertAlmostEqual(state.alpha_roll, expected_moment / sus.Ix)
            self.assertEqual(state.dF_roll, 0)
            self.assertEqual((state.left.azu, state.right.azu), (0, 0))
            self.assertGreater(state.F_frame_cmd, 0)
            self.assertGreater(state.a_frame, 0)
            direct = batch_cases.lr_state(0.001)
            direct.ay = state.ay
            LR_model.Half_suspension_model(sus, direct)
            self.assertAlmostEqual(direct.Mx, expected_moment)

    def test_undamped_step_matches_closed_form_and_converges_with_smaller_time_step(self):
        sus = make_suspension("LR", VEHICLE | {"zeta_frame": 0})
        command = 12 * (2 * sus.ms) * sus.h_rc / sus.track
        omega = np.sqrt(sus.k_frame / sus.m_frame)
        errors = []
        for dt in (0.0001, 0.00005):
            data = self.simulate_step(sus, dt)
            expected = command * (1 - np.cos(omega * data["t"]))
            error = np.max(np.abs(data["dF_roll"] - expected))
            self.assertLess(error, 0.004 * command)
            errors.append(error)
            np.testing.assert_allclose(data["F_frame_spring"], data["dF_roll"])
            np.testing.assert_array_equal(data["F_frame_damper"], 0)
        self.assertLess(errors[1], 0.6 * errors[0])

    def test_damped_branch_matches_independent_second_order_ode(self):
        sus = make_suspension("LR", VEHICLE)
        data = self.simulate_step(sus, 0.00005)
        command = 12 * (2 * sus.ms) * sus.h_rc / sus.track

        def ode(time, state):
            x, velocity = state
            return velocity, (command - sus.k_frame * x - sus.c_frame * velocity) / sus.m_frame

        solution = solve_ivp(ode, (0, data["t"][-1]), [0, 0], t_eval=data["t"], rtol=1e-10, atol=1e-12)
        self.assertTrue(solution.success)
        expected = sus.k_frame * solution.y[0] + sus.c_frame * solution.y[1]
        np.testing.assert_allclose(data["dF_roll"], expected, rtol=0, atol=0.004 * command)

    def test_zero_rc_does_not_excitate_the_frame_branch(self):
        sus = make_suspension("LR", VEHICLE | {"hl_front_roll_center_m": 0, "hl_rear_roll_center_m": 0})
        data = self.simulate_step(sus, 0.001)
        for name in ("F_frame_cmd", "dF_roll", "d_frame", "v_frame", "a_frame"):
            np.testing.assert_array_equal(data[name], 0)

    def test_all_compliant_lr_cases_remain_finite_and_preserve_force_balance(self):
        for scenario in batch_cases.FAMILIES["LR"].scenarios:
            with self.subTest(scenario=scenario):
                sus = make_suspension("LR", VEHICLE)
                sus, state, road, model, config = batch_runner.prepare_case(
                    "LR", "rollcenter_all", scenario, suspension=sus,
                )
                data = batch_runner.simulate_case(sus, state, road, model, config).result()
                self.assertTrue(all(np.isfinite(values).all() for values in data.values()))
                np.testing.assert_allclose(data["dF_roll_l"] + data["dF_roll_r"], 0)
                np.testing.assert_allclose(
                    sus.mu * (data["left_azu"] + data["right_azu"]),
                    data["left_Fs"] + data["right_Fs"] - data["left_Ft"] - data["right_Ft"], atol=1e-10,
                )
                np.testing.assert_allclose(
                    sus.m_frame * data["a_frame"] + data["dF_roll"], data["F_frame_cmd"], atol=1e-10,
                )
                self.assertEqual(len(data["F_frame_cmd"]), len(data["t"]))


if __name__ == "__main__":
    unittest.main()
