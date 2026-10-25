"""Roll-center flow, closed-form dynamics, boundary cases and result export."""

from contextlib import redirect_stdout
from html import unescape
from io import StringIO
import os
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import solve_ivp

from analysis.roll_center_analysis.models import Axle, amplitudes, make_axle, response, sweep, time_grid
from analysis.roll_center_analysis.workflow import DEFAULTS, PARAMETERS, SCAN_SETTINGS
from app.analysis_data import load_analysis_parameters, parse_analysis_parameters
from app.analysis_result import load_plot_choices, save_analysis_result
from main import MainWindow
from app.plugin_loader import scan_analysis

ROOT = Path(__file__).resolve().parents[1]
STAGES = ("roll_center", "roll_center_min_load_f", "roll_center_same_load_r")
VEHICLE = {"ms": 260.0, "h_cog": 0.3, "hl_sprung_front_weight_ratio": 0.43,
           "cog_total_Ixx_kg_m2": 20.0, "Ks_roll_N_per_m": 24000.0,
           "t": 1.25, "hl_rear_track_m": 1.2, "hl_front_roll_motion_ratio": 0.7,
           "hl_rear_roll_motion_ratio": 0.65, "hl_rear_roll_spring_ratio": 0.75, "ay": 2.2}


class RollCenterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plugins = {plugin.plugin_id: plugin for plugin in scan_analysis()}
        cls.flow = MainWindow.load_flow(SimpleNamespace(plugins_by_id=cls.plugins))

    def run_stage(self, stage, values):
        with redirect_stdout(StringIO()):
            return self.plugins[stage].run(parse_analysis_parameters(values, self.plugins[stage].parameters))

    def test_exact_requested_edges_and_selected_upstream_sources(self):
        captures = []
        window = SimpleNamespace(flow=self.flow, flow_view=SimpleNamespace(setHtml=captures.append),
                                 plugins_by_id=self.plugins,
                                 parameter_values=load_analysis_parameters(ROOT / "data/analysis_parameters.csv"))
        MainWindow.build_flow_buttons(window)
        source = unescape(re.search(r'<div class="mermaid">(.*?)</div>', captures[0], re.S).group(1))
        names = {f"flow_node_{i}": row["node_id"] for i, row in enumerate(self.flow)}
        edges = {(names[a], names[b]) for a, b in re.findall(r"(flow_node_\d+) --> (flow_node_\d+)", source)}
        self.assertEqual({edge for edge in edges if set(edge) & set(STAGES)}, {
            ("overall_rigidity", STAGES[0]), (STAGES[0], STAGES[1]), (STAGES[1], STAGES[2]),
            (STAGES[2], "hl_roll")})
        for selected in STAGES:
            rows = MainWindow._required_analysis_rows(window, selected)
            ids = [row["node_id"] for row in rows]
            self.assertIn("cog_movable", ids)
            self.assertIn("tire_stiffness", ids)
            self.assertIn("overall_rigidity", ids)
            self.assertEqual(ids[-1], selected)
            self.assertEqual(ids[-(STAGES.index(selected) + 2):],
                             ["overall_rigidity", *STAGES[:STAGES.index(selected) + 1]])
        self.assertTrue({"rc_front_optimal_height_m", "rc_front_min_peak_rate_N_per_s"}
                        <= self.plugins[STAGES[2]].hidden_parameters)
        self.assertIn("hl_front_roll_center_m", self.plugins[STAGES[1]].outputs)
        self.assertIn("hl_rear_roll_center_m", self.plugins[STAGES[2]].outputs)
        roll_ids = [row["node_id"] for row in MainWindow._required_analysis_rows(window, "hl_roll")]
        self.assertLess(roll_ids.index(STAGES[2]), roll_ids.index("hl_roll"))

    def test_plugin_imports_have_no_figures_and_defaults_are_in_csv(self):
        before = set(plt.get_fignums())
        scan_analysis()
        self.assertEqual(before, set(plt.get_fignums()))
        for filename in ("analysis_parameters.csv", "analysis_parameters_last_set.csv"):
            values = load_analysis_parameters(ROOT / "data" / filename)
            for name, expected in DEFAULTS.items():
                self.assertIn(name, values)
                if filename == "analysis_parameters.csv":
                    self.assertAlmostEqual(float(values[name]), expected)
        for stage in STAGES:
            self.assertTrue(set(SCAN_SETTINGS).isdisjoint(PARAMETERS[stage]))

    def test_normalized_curve_and_minimum_match_the_original_quadratic(self):
        result = self.run_stage("roll_center", DEFAULTS)
        try:
            data = result.tables["roll_center_stiffness.csv"]
            self.assertEqual(len(data), 300)
            np.testing.assert_allclose(data.normalized_stiffness, (1 - data.rc_height_ratio)**2 + 10 * data.rc_height_ratio**2)
            self.assertAlmostEqual(result.outputs["rc_normalized_optimal_ratio"], 1 / 11)
            self.assertAlmostEqual(result.outputs["rc_normalized_min_stiffness"], 10 / 11)
        finally:
            result.close()

    def test_edited_chassis_ratio_reaches_every_roll_center_stage(self):
        ratio = 3.5
        values = VEHICLE | {"rc_chassis_stiffness_ratio": str(ratio)}
        for stage in STAGES:
            with self.subTest(stage=stage):
                self.assertIn("rc_chassis_stiffness_ratio", self.plugins[stage].parameters)
                self.assertNotIn("rc_chassis_stiffness_ratio", self.plugins[stage].hidden_parameters)
                result = self.run_stage(stage, values)
                try:
                    if stage == "roll_center":
                        self.assertAlmostEqual(result.outputs["rc_normalized_optimal_ratio"], 1 / (1 + ratio))
                    else:
                        table = "axle_model.csv" if stage == "roll_center_min_load_f" else "axle_models.csv"
                        axles = result.tables[table]
                        np.testing.assert_allclose(axles.chassis_rate / axles.spring_rate, ratio)
                    values.update(result.outputs)
                finally:
                    result.close()

    def test_analytical_forces_match_independent_ode_solution(self):
        axle = Axle(100, 8, 1.2, 0.3, 1200, 12000)
        times = np.linspace(0, 1, 1001)
        rc, acceleration = 0.08, -12.0

        def ode(time, state):
            phi, velocity, frame, frame_velocity = state
            roll_moment = acceleration * axle.mass * (axle.height - rc) - axle.spring_rate * axle.track**2 * phi
            frame_force = -acceleration * axle.mass * rc / axle.track - axle.chassis_rate * frame
            return [velocity, roll_moment / axle.inertia, frame_velocity, frame_force / (axle.mass / 2)]

        solution = solve_ivp(ode, (0, 1), [0, 0, 0, 0], t_eval=times, rtol=1e-10, atol=1e-12)
        self.assertTrue(solution.success)
        calculated = response(axle, rc, acceleration, times)
        np.testing.assert_allclose(calculated["suspension_transfer_N"],
                                   -axle.spring_rate * axle.track * solution.y[0], rtol=1e-7, atol=1e-6)
        np.testing.assert_allclose(calculated["chassis_transfer_N"], axle.chassis_rate * solution.y[2], rtol=1e-7, atol=1e-6)

    def test_mass_inertia_stiffness_and_quasi_static_force_balance(self):
        p = DEFAULTS | VEHICLE
        front, rear = make_axle(p), make_axle(p, rear=True)
        self.assertAlmostEqual(front.mass + rear.mass, VEHICLE["ms"])
        self.assertAlmostEqual(front.inertia, VEHICLE["cog_total_Ixx_kg_m2"] / 2)
        self.assertAlmostEqual(rear.inertia, VEHICLE["cog_total_Ixx_kg_m2"] / 2)
        self.assertAlmostEqual(rear.spring_rate / front.spring_rate, 0.75 * (0.65 / 0.7)**2)
        for rc in (0, front.height / 2, front.height):
            spring, chassis = amplitudes(front, rc, -10)
            self.assertAlmostEqual(spring + chassis, 10 * front.mass * front.height / front.track)

    def test_zero_paths_and_coarse_time_sampling_do_not_lose_the_first_peak(self):
        p = DEFAULTS | SCAN_SETTINGS | VEHICLE | {"rc_time_step_s": 0.5}
        axle = make_axle(p)
        times = time_grid(p, axle)
        for rc in (0, axle.height):
            result = response(axle, rc, -10, times)
            spring, chassis = amplitudes(axle, rc, -10)
            expected = spring * axle.roll_frequency + chassis * axle.chassis_frequency
            self.assertAlmostEqual(result["peak_rate_N_per_s"], expected, delta=expected * 1e-10)
            self.assertTrue(np.isfinite(result["total_first_pulse_rate_N_per_s"]).all())
        np.testing.assert_allclose(sweep(axle, np.array([0, 0.5, 1]), 0, times), 0)

    def test_front_minimum_is_used_as_rear_target_and_exports_work(self):
        values = DEFAULTS | SCAN_SETTINGS | VEHICLE
        with TemporaryDirectory(dir=ROOT) as temporary:
            destination = Path(temporary)
            for stage in STAGES:
                result = self.run_stage(stage, values)
                try:
                    self.assertEqual(set(result.outputs), set(self.plugins[stage].outputs))
                    self.assertTrue(all(np.isfinite(value) for value in result.outputs.values()))
                    if stage == "roll_center_min_load_f":
                        data = result.tables["front_roll_center_sweep.csv"]
                        self.assertAlmostEqual(result.outputs["rc_front_min_peak_rate_N_per_s"], data.peak_rate_N_per_s.min())
                    if stage == "roll_center_same_load_r":
                        data = result.tables["rear_roll_center_sweep.csv"]
                        np.testing.assert_allclose(data.front_target_peak_rate_N_per_s, values["rc_front_min_peak_rate_N_per_s"])
                        self.assertAlmostEqual(result.outputs["rc_rear_match_error_N_per_s"], data.absolute_error_N_per_s.min())
                    for figure in (result.figure, *result.figures.values()):
                        self.assertLessEqual(len(figure.axes), 4)
                    parameters = parse_analysis_parameters(values, self.plugins[stage].parameters)
                    save_analysis_result(destination, stage, parameters, result)
                    self.assertEqual(len(load_plot_choices(destination / stage)), 1 + len(result.figures))
                    rendered = (destination / stage / "analysis.rendered.html").read_text(encoding="utf-8")
                    self.assertNotIn('class="math-source"', rendered)
                    values.update(result.outputs)
                finally:
                    result.close()

    def test_invalid_inputs_fail_before_creating_figures(self):
        base = DEFAULTS | SCAN_SETTINGS | VEHICLE
        cases = ({"rc_chassis_stiffness_ratio": 0}, {"h_cog": 0}, {"cog_total_Ixx_kg_m2": np.nan},
                 {"rc_front_optimal_height_m": 0.31}, {"hl_sprung_front_weight_ratio": 1})
        for changes in cases:
            before = set(plt.get_fignums())
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.run_stage("roll_center_min_load_f", base | changes)
            self.assertEqual(before, set(plt.get_fignums()))


if __name__ == "__main__":
    unittest.main()
