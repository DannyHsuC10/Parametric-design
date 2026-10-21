"""Validate the new steering flow, source formulas, and linear ODE response."""

from contextlib import redirect_stdout
import csv
import html
import importlib
from io import StringIO
import os
from pathlib import Path
import re
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg import expm
from PySide6.QtWidgets import QApplication, QFormLayout, QWidget

from analysis.cornering.models import (
    ackermann_angles, bicycle_ode, bicycle_step_response, cornering_speed, turning_radius,
)
from analysis_data import load_analysis_parameters, parse_analysis_parameters
from main import MainWindow
from plugin_loader import scan_analysis

ROOT = Path(__file__).resolve().parents[1]
NEW_IDS = ("speed_vs_r", "turning_radius", "ideal_ackemann", "bicycle_model")


class CorneringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plugins = {item.plugin_id: item for item in scan_analysis()}
        cls.values = load_analysis_parameters(ROOT / "data" / "analysis_parameters.csv")
        with redirect_stdout(StringIO()):
            for name in ("cog_movable", "skidpad_test"):
                plugin = cls.plugins[name]
                result = plugin.run(parse_analysis_parameters(cls.values, plugin.parameters))
                try:
                    _, outputs = result
                    cls.values.update({key: str(value) for key, value in outputs.items()})
                finally:
                    if hasattr(result, "close"):
                        result.close()
                    else:
                        plt.close(result[0])

    def run_plugin(self, name, overrides=None):
        plugin = self.plugins[name]
        parameters = parse_analysis_parameters(self.values | (overrides or {}), plugin.parameters)
        with redirect_stdout(StringIO()):
            return plugin.run(parameters)

    def test_requested_flow_paths_and_actual_data_sources_resolve(self):
        window = SimpleNamespace(plugins_by_id=self.plugins)
        with patch("main.QMessageBox.critical") as errors:
            flow = MainWindow.load_flow(window)
        errors.assert_not_called()
        self.assertEqual({row["analysis_id"] for row in flow}, set(self.plugins))
        captures = []
        window.flow, window.parameter_values = flow, self.values
        window.flow_view = SimpleNamespace(setHtml=captures.append)
        MainWindow.build_flow_buttons(window)
        source = html.unescape(re.search(r'<div class="mermaid">(.*?)</div>', captures[0], re.S).group(1))
        ids = {row["node_id"]: f"flow_node_{index}" for index, row in enumerate(flow)}
        edges = set(re.findall(r"(flow_node_\d+) --> (flow_node_\d+)", source))
        self.assertIn('subgraph flow_group_', source)
        self.assertIn('["轉向分析"]', source)
        self.assertIn('stroke:#444444,stroke-width:3px', source)
        self.assertEqual({row["flow_group"] for row in flow if row["node_id"] in {
            "speed_vs_r", "turning_radius", "slalom", "ideal_ackemann", "bicycle_model"
        }}, {"轉向分析"})
        for first, second in (("track_analysis", "speed_vs_r"), ("speed_vs_r", "turning_radius"),
                              ("turning_radius", "slalom"),
                              ("turning_radius", "ideal_ackemann"),
                              ("ideal_ackemann", "bicycle_model")):
            self.assertIn((ids[first], ids[second]), edges)
        self.assertNotIn((ids["speed_vs_r"], ids["track_analysis"]), edges)
        self.assertNotIn((ids["speed_vs_r"], ids["skidpad_test"]), edges)
        self.assertNotIn((ids["track_analysis"], ids["skidpad_test"]), edges)
        required = MainWindow._required_analysis_rows(window, "bicycle_model")
        names = [row["node_id"] for row in required]
        self.assertLess(names.index("cog_movable"), names.index("bicycle_model"))
        self.assertNotIn("skidpad_test", names)

    def test_importing_each_new_plugin_has_no_plot_or_loader_side_effects(self):
        before = set(plt.get_fignums())
        with redirect_stdout(StringIO()) as output, patch.object(plt, "show") as show:
            for name in ("speed_vs_R", "Turning_Radius", "ideal_ackemann", "Bicycle_Model"):
                importlib.reload(importlib.import_module("analysis." + name))
        self.assertEqual(output.getvalue(), "")
        self.assertEqual(set(plt.get_fignums()), before)
        show.assert_not_called()

    def test_cornering_limit_obeys_lateral_force_balance(self):
        radius = np.array([3.0, 9.125, 50.0])
        speed = cornering_speed(radius, 1.7)
        np.testing.assert_allclose(speed**2 / radius, 1.7 * 9.81)
        np.testing.assert_allclose(cornering_speed(radius * 4, 1.7), speed * 2)

    def test_steering_and_ackermann_geometry_match_one_turning_center(self):
        radius = np.array([5.0, 10.0, 30.0])
        inner, outer = ackermann_angles(radius, 1.53, 1.25)
        self.assertTrue(np.all(inner > outer))
        np.testing.assert_allclose(1.53 / np.tan(inner) + 1.25 / 2, radius)
        np.testing.assert_allclose(1.53 / np.tan(outer) - 1.25 / 2, radius)
        angle = np.array([10.0, 25.0, 45.0])
        np.testing.assert_allclose(np.rad2deg(np.arctan(1.53 / turning_radius(angle, 1.53))), angle)

    def test_bicycle_response_matches_matrix_exponential_across_the_step(self):
        vx, mass, inertia, lf, lr, cf, cr = 12, 320, 95, 0.8, 0.7, 40000, 35000
        angle, start = np.deg2rad(5), 0.5
        times = np.linspace(0, 2, 101)
        actual = bicycle_step_response(times, start, angle, vx, mass, inertia, lf, lr, cf, cr)
        augmented = np.zeros((3, 3))
        augmented[:2, :2] = [
            [-(cf + cr) / (mass * vx), (-cf * lf + cr * lr) / (mass * vx) - vx],
            [(-lf * cf + lr * cr) / (inertia * vx), -(lf**2 * cf + lr**2 * cr) / (inertia * vx)],
        ]
        augmented[:2, 2] = np.array([cf / mass, lf * cf / inertia]) * angle
        for index, time in enumerate(times):
            expected = (expm(augmented * max(0, time - start)) @ [0, 0, 1])[:2]
            np.testing.assert_allclose(actual[:, index], expected, rtol=2e-7, atol=2e-9)
        np.testing.assert_array_equal(actual[:, times <= start], 0)
        steady = -np.linalg.solve(augmented[:2, :2], augmented[:2, 2])
        np.testing.assert_allclose(bicycle_ode(2, steady, lambda time: angle,
                                             vx, mass, inertia, lf, lr, cf, cr), 0, atol=1e-12)

    def test_all_new_plugins_preserve_source_sample_counts_and_return_finite_results(self):
        for name, count, axes in zip(NEW_IDS, (200, 500, 51, 1000), (1, 1, 2, 3)):
            result = self.run_plugin(name)
            try:
                self.assertEqual(set(result.outputs), set(self.plugins[name].outputs))
                self.assertTrue(all(np.isfinite(value) for value in result.outputs.values()))
                self.assertEqual(len(result.figure.axes), axes)
                frame = next(iter(result.tables.values()))
                self.assertEqual(len(frame), count)
                self.assertTrue(np.isfinite(frame.to_numpy()).all())
                if name == "bicycle_model":
                    self.assertAlmostEqual(result.outputs["bicycle_front_cg_distance_m"]
                                           + result.outputs["bicycle_rear_cg_distance_m"], float(self.values["L"]))
            finally:
                result.close()

    def test_vehicle_max_steering_marker_uses_exact_angle_and_keeps_the_sweep_fixed(self):
        self.assertEqual(set(self.plugins["turning_radius"].parameters),
                         {"L", "vehicle_max_steering_angle_deg"})
        for angle in (37.25, 75.0):
            result = self.run_plugin("turning_radius", {"vehicle_max_steering_angle_deg": str(angle)})
            try:
                expected_radius = float(self.values["L"]) / np.tan(np.deg2rad(angle))
                frame = result.tables["turning_radius.csv"]
                self.assertEqual(len(frame), 500)
                self.assertEqual(frame.steering_angle_deg.iloc[0], 10)
                self.assertEqual(frame.steering_angle_deg.iloc[-1], 60)
                axis = result.figure.axes[0]
                np.testing.assert_allclose(axis.collections[0].get_offsets(), [[angle, expected_radius]])
                self.assertIn(f"{angle:.2f}°", axis.texts[0].get_text())
                self.assertIn(f"{expected_radius:.3f} m", axis.texts[0].get_text())
                self.assertAlmostEqual(result.outputs["turning_radius_at_max_steering_m"], expected_radius)
                self.assertGreater(axis.get_xlim()[1], angle)
                self.assertGreater(axis.get_ylim()[1], expected_radius)
            finally:
                result.close()

    def test_bicycle_manual_speed_is_editable_and_independent_of_skidpad_outputs(self):
        plugin = self.plugins["bicycle_model"]
        self.assertNotIn("v_ref", plugin.parameters)
        self.assertIn("vehicle_max_steering_angle_deg", plugin.parameters)
        self.assertNotIn("bicycle_steering_step_deg", plugin.parameters)
        fixed_names = {"bicycle_step_time_s", "bicycle_duration_s", "num_points_bicycle"}
        self.assertFalse(fixed_names.intersection(plugin.parameters))
        values = self.values | {"bicycle_v_ref_kmh": "72", "v_ref": "999"}
        parameters = parse_analysis_parameters(values, plugin.parameters)
        with patch.object(plugin.module, "bicycle_step_response", wraps=bicycle_step_response) as solve:
            with redirect_stdout(StringIO()):
                result = plugin.run(parameters)
        try:
            self.assertEqual(solve.call_args.args[3], 20.0)  # 72 km/h -> 20 m/s.
            frame = result.tables["bicycle_response.csv"]
            self.assertEqual(len(frame), 1000)
            self.assertEqual(frame.time_s.iloc[-1], 5.0)
            np.testing.assert_array_equal(frame.loc[frame.time_s <= 0.5, "steering_deg"], 0)
        finally:
            result.close()
        self.__class__.app = QApplication.instance() or QApplication([])
        host = QWidget()
        window = SimpleNamespace(
            parameter_form=QFormLayout(host), parameter_edits={}, parameter_values=values,
            output_names={name for item in self.plugins.values() for name in item.outputs},
            update_parameter=lambda name, value: None,
        )
        try:
            MainWindow.build_parameter_fields(window, plugin)
            self.assertEqual(window.parameter_edits["bicycle_v_ref_kmh"].text(), "72")
            self.assertFalse(window.parameter_edits["bicycle_v_ref_kmh"].isReadOnly())
            self.assertFalse(fixed_names.intersection(window.parameter_edits))
        finally:
            host.close()

    def test_invalid_physical_inputs_are_rejected_before_plotting(self):
        for name, overrides in (
            ("speed_vs_r", {"mu_w": "nan"}),
            ("turning_radius", {"vehicle_max_steering_angle_deg": "90"}),
            ("ideal_ackemann", {"t": "6"}),
            ("bicycle_model", {"bicycle_front_cornering_stiffness_N_per_rad": "0"}),
            ("bicycle_model", {"bicycle_v_ref_kmh": "0"}),
            ("bicycle_model", {"hl_front_weight_ratio": "1"}),
        ):
            with self.subTest(name=name, overrides=overrides), self.assertRaises(ValueError):
                self.run_plugin(name, overrides)


if __name__ == "__main__":
    unittest.main()
