"""Aero force balance, angle units, upstream coefficient transfer and exports."""

import csv
from contextlib import redirect_stdout
from io import StringIO
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from analysis.aerodynamics.model import ModalAeroModel
from analysis.aerodynamics.parameters import DEFAULTS, make_model
from app.analysis_data import load_analysis_parameters, parse_analysis_parameters
from app.analysis_result import load_plot_choices, save_analysis_result
from app.flow_diagram import flow_edges, render_flow_diagram
from app.plugin_loader import scan_analysis
from main import MainWindow


ROOT = Path(__file__).resolve().parents[1]


class AerodynamicsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plugins = {plugin.plugin_id: plugin for plugin in scan_analysis()}
        with (ROOT / "data/analysis_flow.csv").open(encoding="utf-8-sig", newline="") as stream:
            cls.flow = list(csv.DictReader(stream))
        cls.values = DEFAULTS | {"Cl": 2.4, "v_ref": 60.12, "A_air": 1.2, "L": 1.55, "t": 1.25}

    def run_stage(self, stage, values):
        plugin = self.plugins[stage]
        with redirect_stdout(StringIO()):
            return plugin.run(parse_analysis_parameters(values, plugin.parameters))

    def test_force_balance_cop_moments_and_speed_squared_scaling(self):
        model = ModalAeroModel()
        pitch, roll = np.deg2rad([1.2, -2.3])
        first = model.calculate_from_modal(10, -0.01, pitch, roll)
        second = model.calculate_from_modal(20, -0.01, pitch, roll)
        forces = [first[name] for name in ("F_FL", "F_FR", "F_RL", "F_RR")]
        self.assertAlmostEqual(sum(forces), first["F_down"])
        self.assertAlmostEqual((forces[0] + forces[1] - forces[2] - forces[3]) * model.wheelbase / 2,
                               first["F_down"] * first["COP_x"])
        self.assertAlmostEqual((forces[0] + forces[2] - forces[1] - forces[3]) * model.track / 2,
                               first["F_down"] * first["COP_y"])
        for name in ("F_down", "F_drag", "F_FL", "F_FR", "F_RL", "F_RR"):
            self.assertAlmostEqual(second[name], 4 * first[name])
        self.assertAlmostEqual(second["COP_x"], first["COP_x"])
        self.assertAlmostEqual(second["COP_y"], first["COP_y"])

    def test_signed_angles_preserve_symmetric_downforce_and_shift_cop(self):
        model = ModalAeroModel()
        angle = np.deg2rad(2)
        positive = model.calculate_from_modal(16.7, -0.01, angle, angle)
        negative = model.calculate_from_modal(16.7, -0.01, -angle, -angle)
        self.assertAlmostEqual(positive["F_down"], negative["F_down"])
        nominal = model.wheelbase * (model.front_balance - 0.5)
        self.assertAlmostEqual(positive["COP_x"] - nominal, nominal - negative["COP_x"])
        self.assertAlmostEqual(positive["COP_y"], -negative["COP_y"])
        self.assertAlmostEqual(positive["COP_y"], model.track * model.K_balance_roll * angle)

    def test_zero_speed_and_lift_sign_are_preserved(self):
        for cl0 in (-2.4, 2.4):
            model = ModalAeroModel(CL0=cl0)
            values = model.calculate_from_modal(0, 0, 0.1, 0.2)
            for name in ("F_down", "F_drag", "COP_x", "COP_y", "F_FL", "F_FR", "F_RL", "F_RR"):
                self.assertEqual(values[name], 0)
            self.assertEqual(np.sign(model.calculate_from_modal(10, 0, 0, 0)["F_down"]), -np.sign(cl0))

    def test_estimated_cl_reproduces_upstream_reference_downforce(self):
        figure, outputs = self.run_stage("aero_cl_cd", {"F_ref": 715, "v_ref": 43, "A_air": 2})
        plt.close(figure)
        values = self.values | outputs | {"A_air": 2, "v_ref": 43, "aero_heave_m": 0}
        result = self.run_stage("aero_roll_pitch_analysis", values)
        try:
            self.assertEqual(result.outputs["aero_model_CL0"], -outputs["Cl"])
            self.assertAlmostEqual(result.outputs["aero_modal_baseline_downforce_N"], 715)
        finally:
            result.close()

    def test_both_nodes_are_registered_in_the_requested_flow_and_resolve_sources(self):
        edges = set(flow_edges(self.flow))
        self.assertIn(("aero_cl_cd", "aero_roll_pitch_analysis"), edges)
        self.assertIn(("aero_roll_pitch_analysis", "aero_3d"), edges)
        self.assertEqual([int(row["order"]) for row in self.flow], list(range(1, len(self.flow) + 1)))
        self.assertEqual({row["analysis_id"] for row in self.flow}, set(self.plugins))
        values = {name: value for plugin in self.plugins.values() for name, value in plugin.parameter_defaults.items()}
        values.update(load_analysis_parameters(ROOT / "data/analysis_parameters.csv"))
        window = SimpleNamespace(flow=self.flow, plugins_by_id=self.plugins, parameter_values=values)
        required = [row["node_id"] for row in MainWindow._required_analysis_rows(window, "aero_3d")]
        for source, target in (("cog_movable", "aero_roll_pitch_analysis"),
                               ("aero_cl_cd", "aero_roll_pitch_analysis"), ("aero_roll_pitch_analysis", "aero_3d")):
            self.assertLess(required.index(source), required.index(target))
        html = render_flow_diagram(self.flow, "aero 分析")
        self.assertIn("aero 3D", html)
        self.assertIn("aero_roll_pitch_analysis", html)
        for stage in ("aero_roll_pitch_analysis", "aero_3d"):
            plugin = self.plugins[stage]
            self.assertTrue(all("new" not in Path(path).parts for path in plugin.input_files))
            self.assertIn("v_ref", plugin.parameters)
            self.assertIn("v_ref", plugin.hidden_parameters)
            self.assertNotIn("aero_speed_m_s", plugin.parameters)
            self.assertNotIn("aero_speed_m_s", plugin.parameter_defaults)

    def test_invalid_operating_points_fail_before_plotting(self):
        cases = ({"A_air": 0}, {"L": 0}, {"v_ref": -1}, {"Cl": np.nan},
                 {"aero_angle_min_deg": 4}, {"aero_surface_points": 3.5}, {"aero_curve_points": 2},
                 {"aero_front_balance": 1.2}, {"aero_K_balance_roll": 100},
                 {"aero_CD0": -1}, {"aero_Kd_p": -100})
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                make_model(self.values | changes)

    def test_surface_exports_preserve_every_panel_and_exact_zero_angle_sections(self):
        curves = self.run_stage("aero_roll_pitch_analysis", self.values)
        values = self.values | curves.outputs
        result = self.run_stage("aero_3d", values)
        try:
            self.assertEqual(set(result.outputs), set(self.plugins["aero_3d"].outputs))
            self.assertEqual(len(result.tables["aero_surface.csv"]), 900)
            self.assertEqual(len(result.figures), 12)
            self.assertTrue(all(np.isfinite(value) for value in result.outputs.values()))
            expected_drag = 0.5 * 1.225 * values["A_air"] * (values["v_ref"] / 3.6)**2 * values["aero_CD0"]
            self.assertAlmostEqual(result.outputs["aero_3d_drag_mean_N"], expected_drag)
            self.assertTrue(all(1 <= len(figure.axes) <= 4 for figure in (result.figure, *result.figures.values())))
            pitch, roll = result.tables["pitch_section.csv"], result.tables["roll_section.csv"]
            np.testing.assert_array_equal(pitch.roll_deg, 0)
            np.testing.assert_array_equal(roll.pitch_deg, 0)
            self.assertAlmostEqual(result.outputs["aero_3d_dCOP_x_dpitch_m_per_rad"], 1.55 * 0.2)
            self.assertAlmostEqual(result.outputs["aero_3d_dCOP_y_droll_m_per_rad"], 1.25 * 0.1)
            with TemporaryDirectory(dir=ROOT) as temporary:
                save_analysis_result(temporary, "aero_3d", values, result)
                folder = Path(temporary) / "aero_3d"
                self.assertEqual(len(load_plot_choices(folder)), 13)
                with (folder / "aero_surface.csv").open(encoding="utf-8-sig", newline="") as stream:
                    self.assertEqual(len(list(csv.DictReader(stream))), 900)
        finally:
            curves.close()
            result.close()


if __name__ == "__main__":
    unittest.main()
