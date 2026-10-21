"""Physics and integration checks for the five-group high/low damping workflow."""

import csv
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
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QComboBox, QDialog, QTableWidget, QWidget

from analysis_data import load_analysis_parameters, parse_analysis_parameters
from analysis_result import normalize_result, save_analysis_result
from analysis.hl_damping.frequency import frequency_response
from analysis.hl_damping.parameters import GROUPS, STAGES
from analysis.hl_damping.workflow import build_models, response_metrics, simulate_lateral
from analysis.hl_damping.vehicle import make_vehicle
from main import MainWindow
from plugin_loader import scan_analysis


ROOT = Path(__file__).resolve().parents[1]


class HLDampingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.values = load_analysis_parameters(ROOT / "data" / "analysis_parameters.csv")
        cls.plugins = {plugin.plugin_id: plugin for plugin in scan_analysis()}
        cls.results = {}
        with redirect_stdout(StringIO()):
            for stage in ("compressed_travel", "aero_stiffness", "frequency_stiffness", "tire_stiffness", *STAGES):
                plugin = cls.plugins[stage]
                parameters = parse_analysis_parameters(cls.values, plugin.parameters)
                result = normalize_result(plugin.run(parameters))
                cls.values.update({key: str(value) for key, value in result.outputs.items()})
                if stage in STAGES:
                    cls.results[stage] = result
                plt.close(result.figure)
        parameters = parse_analysis_parameters(cls.values, cls.plugins["hl_ode"].parameters)
        cls.models = build_models(parameters)
        with (ROOT / "data" / "analysis_flow.csv").open(encoding="utf-8-sig", newline="") as stream:
            cls.flow = list(csv.DictReader(stream))

    def test_all_ten_plugins_return_finite_outputs_and_complete_data(self):
        self.assertEqual(len(self.results), 10)
        for stage, result in self.results.items():
            with self.subTest(stage=stage):
                self.assertEqual(set(result.outputs), set(self.plugins[stage].outputs))
                self.assertTrue(all(np.isfinite(value) for value in result.outputs.values()))
                self.assertTrue(result.tables)
                for axis in result.figure.axes:
                    for line in axis.lines:
                        self.assertTrue(np.all(np.isfinite(line.get_ydata())))

    def test_five_groups_branch_after_damped_oscillation_and_join(self):
        indices = {row["node_id"]: i for i, row in enumerate(self.flow)}
        start = indices["damped_oscillation_analysis"]
        self.assertEqual([row["node_id"] for row in self.flow[start + 1:start + 11]], list(STAGES))
        self.assertEqual({row["flow_group"] for row in self.flow if row["node_id"] in STAGES}, set(GROUPS.values()))
        captures = []
        window = SimpleNamespace(flow=self.flow, flow_view=SimpleNamespace(setHtml=captures.append))
        MainWindow.build_flow_buttons(window)
        source = unescape(re.search(r'<div class="mermaid">(.*?)</div>', captures[0], re.S).group(1))
        self.assertEqual(source.count("subgraph"), len({
            row["flow_group"] for row in self.flow if row.get("flow_group")
        }))
        for stage in ("hl_heave", "hl_roll"):
            self.assertIn(f"flow_node_{start} --> flow_node_{indices[stage]}", source)
        for stage, (_, _, dependencies, _) in STAGES.items():
            for dependency in dependencies:
                self.assertIn(f"flow_node_{indices[dependency]} --> flow_node_{indices[stage]}", source)

    def test_single_ode_run_resolves_all_new_stages_and_spring_sources(self):
        inputs = load_analysis_parameters(ROOT / "data" / "analysis_parameters.csv")
        window = SimpleNamespace(flow=self.flow, plugins_by_id=self.plugins, parameter_values=inputs)
        rows = MainWindow._required_analysis_rows(window, "hl_ode")
        self.assertEqual({row["node_id"] for row in rows}, {
            "compressed_travel", "aero_stiffness", "frequency_stiffness", "tire_stiffness", *STAGES})

    def test_mass_and_heave_stiffness_conventions(self):
        vehicle, heave, *_ = self.models
        self.assertEqual(vehicle.mass_kg, 320)
        self.assertEqual(vehicle.front.sprung_mass_axis_kg + vehicle.rear.sprung_mass_axis_kg, 260)
        for axle, result in ((vehicle.front, heave.front), (vehicle.rear, heave.rear)):
            self.assertLess(result.ride_rate_n_per_m, result.wheel_rate_n_per_m)
            self.assertLess(result.ride_rate_n_per_m, 2 * vehicle.tire_vertical_rate_n_per_m)
            self.assertAlmostEqual(result.critical_damping_n_s_per_m,
                                   2 * np.sqrt(result.wheel_rate_n_per_m * axle.sprung_mass_axis_kg))

    def test_roll_modes_are_mass_normalized_and_damping_targets_match(self):
        _, _, roll, *_ = self.models
        modes = roll.modal.mode_shapes
        np.testing.assert_allclose(modes.T @ roll.mass_matrix @ modes, np.eye(3), atol=1e-12)
        omega = 2 * np.pi * roll.modal.natural_frequencies_hz
        np.testing.assert_allclose(roll.stiffness_matrix @ modes,
                                   roll.mass_matrix @ modes @ np.diag(omega**2), atol=1e-10)
        projected = modes.T @ roll.modal.damping_matrix_low @ modes
        np.testing.assert_allclose(projected, np.diag(2 * roll.modal.target_zeta_low * omega), atol=1e-11)

    def test_physical_roll_dampers_are_passive_and_stable(self):
        state, systems = self.models[4:6]
        fit = state._fit_physical_roll_damping()
        for speed in ("low", "high"):
            matrix = fit[f"{speed}_matrix"]
            self.assertGreaterEqual(np.linalg.eigvalsh(matrix).min(), -1e-9)
            self.assertTrue(np.all(np.linalg.eigvals(getattr(systems, f"roll_physical_{speed}").A).real < 0))
        coefficients = systems.physical_fit.filter(like="linear_damping").to_numpy()
        self.assertTrue(np.all(coefficients >= 0))

    def test_frequency_response_agrees_with_static_gain(self):
        state, systems = self.models[4:6]
        for system in (systems.roll_modal_low, systems.roll_physical_low, systems.roll_1dof_low,
                       state.heave_system(self.models[0].front, self.models[1].front)):
            _, response = frequency_response(system, [1e-8])
            static = (system.C @ np.linalg.solve(-system.A, system.B) + system.D).item()
            self.assertAlmostEqual(response[0].real, static, places=10)

    def test_independent_wheel_settings_preserve_axis_heave_and_roll(self):
        vehicle, heave, roll, independent, *_ = self.models
        for axle, heave_axis, roll_axis, single in (
            (vehicle.front, heave.front, roll.front, independent.front),
            (vehicle.rear, heave.rear, roll.rear, independent.rear),
        ):
            self.assertAlmostEqual(2 * single.wheel_rate_n_per_m, heave_axis.wheel_rate_n_per_m)
            self.assertAlmostEqual(2 * single.shock_low_speed_damping_n_s_per_m * axle.motion_ratio.independent**2,
                                   heave_axis.low_speed_damping_n_s_per_m)
            self.assertAlmostEqual(single.base_roll_stiffness_n_m_per_rad + single.required_arb_stiffness_n_m_per_rad,
                                   roll_axis.suspension_roll_stiffness_n_m_per_rad)

    def test_shock_dyno_is_continuous_at_both_knees_and_dissipative(self):
        damper = self.models[6]
        for curves in (damper._heave_curves(False), damper._heave_curves(True), damper._roll_physical_curves()):
            for curve in curves.values():
                knee = curve.knee_velocity_mm_s
                for sign in (-1, 1):
                    self.assertAlmostEqual(curve.force(sign * (knee - 1e-8)).item(),
                                           curve.force(sign * (knee + 1e-8)).item(), places=5)
                velocity = np.linspace(-300, 300, 601)
                self.assertTrue(np.all(velocity * curve.force(velocity) >= 0))
                self.assertEqual(curve.force(0).item(), 0)

    def test_quasi_static_and_ode_equilibria_agree(self):
        vehicle, heave, roll, *_ = self.models
        tables = self.results["hl_ode"].tables
        for case, acceleration in (("braking", -vehicle.analysis.ode_braking_g),
                                   ("acceleration", vehicle.analysis.ode_acceleration_g)):
            transfer = acceleration * vehicle.weight_n * vehicle.cg_height_m / vehicle.wheelbase_m
            for topology in ("decoupled", "independent"):
                table = tables[f"ode_{case}_{topology}.csv"]
                self.assertAlmostEqual(table.front_sprung_displacement_m.iloc[-1],
                                       -transfer / heave.front.ride_rate_n_per_m, delta=2e-6)
                self.assertAlmostEqual(table.rear_sprung_displacement_m.iloc[-1],
                                       transfer / heave.rear.ride_rate_n_per_m, delta=2e-6)
                self.assertAlmostEqual((table.front_tire_fz_n + table.rear_tire_fz_n).iloc[-1],
                                       vehicle.weight_n / 2, delta=0.1)
        lateral = tables["ode_cornering_physical.csv"]
        self.assertAlmostEqual(lateral.sprung_roll_deg.iloc[-1],
                               roll.roll_gradient_deg_per_g * vehicle.analysis.roll_step_ay_g, delta=0.002)
        total_fz = lateral.filter(like="_fz_n").sum(axis=1)
        np.testing.assert_allclose(total_fz, vehicle.weight_n, atol=1e-10)

    def test_zero_input_ode_and_unsettled_metrics(self):
        parameters = parse_analysis_parameters(self.values, self.plugins["hl_ode"].parameters)
        parameters["ay"] = 0
        vehicle = make_vehicle(parameters)
        lateral = simulate_lateral(vehicle, self.models[2], self.models[6]._roll_physical_curves())
        np.testing.assert_array_equal(lateral.sprung_roll_deg.to_numpy(), 0)
        self.assertTrue(np.isnan(response_metrics(np.array([0, 1]), [0, 0.5], 1)["settling_2_percent_s"]))
        self.assertEqual(response_metrics(np.array([0, 1]), [0, 0], 0)["settling_2_percent_s"], 0)

    def test_invalid_vehicle_inputs_fail_before_solving(self):
        parameters = parse_analysis_parameters(self.values, self.plugins["hl_ode"].parameters)
        for key, value in (("hl_front_weight_ratio", 1), ("hl_knee_velocity_mm_s", 0),
                           ("hl_front_roll_low_zeta", -1), ("Kt", np.nan)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                make_vehicle(parameters | {key: value})

    def test_export_has_five_reports_and_live_result_gallery(self):
        stage = "hl_heave_response"
        parameters = parse_analysis_parameters(self.values, self.plugins[stage].parameters)
        with TemporaryDirectory(dir=ROOT) as temporary:
            self.assertTrue(Path(temporary).resolve().is_relative_to(ROOT.resolve()))
            save_analysis_result(temporary, stage, parameters, self.results[stage])
            root = Path(temporary)
            reports = list((root / "hl_damping").glob("*.html"))
            self.assertEqual(len(reports), 6)
            html = (root / "hl_damping" / "02_heave_analysis.html").read_text(encoding="utf-8")
            self.assertIn("heave_front_response.png", html)
            for relative in re.findall(r'(?:src|href)="(\.\./[^\"]+)"', html):
                if not relative.endswith("analysis.md"):
                    self.assertTrue((root / "hl_damping" / relative).exists(), relative)
            self.assertTrue((root / stage / "heave_step_metrics.csv").exists())

        app = QApplication.instance() or QApplication([])
        parent = QWidget()
        errors, checked = [], []

        def inspect():
            dialog = parent.findChild(QDialog)
            try:
                self.assertIsNotNone(dialog)
                selectors = dialog.findChildren(QComboBox)
                self.assertEqual(len(selectors), 2)
                self.assertGreater(selectors[0].count(), 1)
                self.assertGreater(selectors[1].count(), 1)
                selectors[0].setCurrentIndex(1)
                selectors[1].setCurrentIndex(1)
                self.assertGreater(dialog.findChild(QTableWidget).rowCount(), 0)
                checked.append(True)
            except BaseException as error:
                errors.append(error)
            finally:
                if dialog:
                    dialog.accept()

        QTimer.singleShot(100, inspect)
        MainWindow.show_result(parent, stage)
        parent.close()
        if errors:
            raise errors[0]
        self.assertTrue(checked)


if __name__ == "__main__":
    unittest.main()
