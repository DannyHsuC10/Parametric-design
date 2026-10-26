"""Full-car migration, isolated road inputs, and app flow integration."""

import csv
import os
from contextlib import redirect_stdout
import importlib.util
from io import StringIO
from pathlib import Path
import unittest
from unittest.mock import patch
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import matplotlib
matplotlib.use("Agg")
import numpy as np

from analysis.full_suspension import workflow
from analysis.full_suspension.suspension_set.Suspension import Suspension_A
from analysis.full_suspension.suspension_set.suspension_state import full_suspension_state
from app.flow_diagram import flow_edges
from app.plugin_loader import scan_analysis
from app.analysis_data import load_analysis_parameters, parse_analysis_parameters
from main import MainWindow

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class FullSuspensionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.logs = {name: workflow.simulate(name) for name in workflow.SCENARIOS}

    def test_both_cases_are_finite_complete_and_independent(self):
        for name, logger in self.logs.items():
            data = logger.result()
            self.assertEqual(len(data["t"]), 1500)
            self.assertAlmostEqual(data["t"][-1], 1.5)
            self.assertTrue(all(np.isfinite(value).all() for value in data.values()))
            self.assertEqual(data["theta"].shape, (1500, 4))
            np.testing.assert_array_equal(data["zs"][0], np.zeros(4))
        acc = self.logs["road_acc"].result()
        bump = self.logs["road_FL_bump"].result()
        self.assertTrue(np.all(acc["zr"] == 0))
        np.testing.assert_array_equal(acc["Fx"][-1], [-1000] * 4)
        np.testing.assert_array_equal(acc["Fy"][-1], [-1000] * 4)
        self.assertEqual(bump["zr"][:, 0].max(), 0.05)
        self.assertTrue(np.all(bump["zr"][:, 1:] == 0))
        self.assertTrue(np.all(bump["Fx"] == 0))
        self.assertTrue(np.all(bump["F_cg"] == 0))

    def test_solver_matches_original_with_requested_tire_damping(self):
        spec = importlib.util.spec_from_file_location("original_full_model", ROOT / "new/model/Suspension_model_v13.py")
        original = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(original)
        # Load the original factory independently. Reusing the migrated factory
        # on both sides would miss accidental changes to default KC parameters.
        factory_spec = importlib.util.spec_from_file_location(
            "analysis.full_suspension.suspension_set._original",
            ROOT / "new/suspension_set/Suspension.py")
        original_factory = importlib.util.module_from_spec(factory_spec)
        factory_spec.loader.exec_module(original_factory)
        for scenario, road in workflow.SCENARIOS.items():
            sus = original_factory.Suspension_A()
            # The requested default is 50 instead of new/'s original 300.
            for tire in sus.tire_list:
                tire.damper.c = 50.0
            state = full_suspension_state(sus)
            expected = workflow.SimulationLogger()
            with redirect_stdout(StringIO()):
                for _ in range(round(workflow.DURATION / workflow.DT)):
                    road(state)
                    original.motion(state, sus)
                    state.Integration(sus)
                    expected.add_state(state)
            for key, values in expected.result().items():
                np.testing.assert_array_equal(self.logs[scenario].result()[key], values, err_msg=f"{scenario}/{key}")

    def test_flow_plugin_and_result_gallery(self):
        with (ROOT / "data/analysis_flow.csv").open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        incoming = {a for a, b in flow_edges(rows) if b == "full_suspension"}
        self.assertEqual(incoming, {"quarter_suspension_model", "half_rollcenter_all_model", "half_suspension_model_fr"})
        plugin = next(item for item in scan_analysis() if item.plugin_id == "full_suspension")
        self.assertTrue(plugin.input_files)
        self.assertTrue(all(Path(path).is_relative_to(ROOT / "analysis/full_suspension") for path in plugin.input_files))
        with patch.object(workflow, "simulate", side_effect=lambda name, parameters: self.logs[name]):
            result = plugin.run({})
        try:
            self.assertEqual(result.outputs["full_suspension_case_count"], 2)
            self.assertEqual(set(result.outputs), set(plugin.outputs))
            for scenario in workflow.SCENARIOS:
                self.assertNotIn(f"{scenario}.gif", result.artifacts)
                self.assertIn(f"{scenario}_response.png", result.figures)
                frame = result.tables[f"{scenario}_timeseries.csv"]
                self.assertEqual(len(frame), 1500)
                self.assertIn("theta_Front_roll", frame)
                self.assertIn("zr_FL", frame)
            self.assertTrue(all(len(fig.axes) <= 4 for fig in (result.figure, *result.figures.values())))
        finally:
            result.close()

    def test_series_heave_matches_designed_working_axle_rate_for_nonunit_mr(self):
        for mr in (0.5, 0.8, 1.2):
            sus = Suspension_A({"Ks_pitch_N_per_m": 80000.0, "MR": mr,
                                "hl_front_roll_motion_ratio": 0.3,
                                "hl_rear_roll_motion_ratio": 0.9,
                                "tender_to_heave_stiffness_ratio": 0.5})
            for kc in sus.shock_list[:4]:
                self.assertEqual(kc.motion_ratio.ratio(0), mr)
            displacement = 1e-5
            forces, _ = workflow.model.shocks_KC_force(
                sus.shock_list, np.array([displacement, displacement, 0, 0]),
                np.zeros(4), np.zeros(4), np.zeros(4))
            state = full_suspension_state(sus)
            corners = workflow.model.Modal_to_corner(forces, state)
            measured_axle_rate = -(corners[0] + corners[1]) / displacement
            self.assertAlmostEqual(measured_axle_rate, 80000 * mr**2)

    def test_roll_stiffness_matches_rc_model_and_damping_matches_selected_ratio(self):
        from analysis.roll_center_analysis.models import make_axle
        p = dict(ms=260.0, cog_total_Ixx_kg_m2=40.0, t=1.25, h_cog=0.3,
                 hl_sprung_front_weight_ratio=0.5, Ks_roll_N_per_m=50000.0,
                 MR=0.6, hl_front_roll_motion_ratio=0.6, rc_chassis_stiffness_ratio=10.0,
                 damped_sweep_selected_ratio_used=0.7)
        axle = make_axle(p)
        sus = Suspension_A(p)
        state = full_suspension_state(sus)
        angle = 1e-5
        rotation = np.array([angle * sus.tf / 2, -angle * sus.tf / 2, 0, 0])
        forces, _ = workflow.model.shocks_KC_force(
            sus.shock_list, rotation, np.zeros(4), np.zeros(4), np.zeros(4))
        corners = workflow.model.Modal_to_corner(forces, state)
        _, moments, _ = workflow.model.corner_to_body(*corners, sus)
        angular_rate = -moments[0] / angle
        self.assertAlmostEqual(angular_rate, axle.spring_rate * axle.track**2)
        forces, _ = workflow.model.shocks_KC_force(
            sus.shock_list, np.zeros(4), np.zeros(4), rotation, np.zeros(4))
        corners = workflow.model.Modal_to_corner(forces, state)
        _, moments, _ = workflow.model.corner_to_body(*corners, sus)
        angular_damping = -moments[0] / angle
        self.assertAlmostEqual(angular_damping / (2 * np.sqrt(angular_rate * sus.I[0])), 0.7)

    def test_heave_damping_matches_working_rate_at_nonunit_mr(self):
        sus = Suspension_A(dict(ms=260.0, Ks_pitch_N_per_m=80000.0, MR=0.6,
                                damped_sweep_selected_ratio_used=0.7))
        state = full_suspension_state(sus)
        velocity = 1e-4
        forces, _ = workflow.model.shocks_KC_force(
            sus.shock_list, np.zeros(4), np.zeros(4),
            np.array([velocity, velocity, 0, 0]), np.zeros(4))
        corners = workflow.model.Modal_to_corner(forces, state)
        damping = -(corners[0] + corners[1]) / velocity
        self.assertAlmostEqual(damping / (2 * np.sqrt(80000 * 0.6**2 * 130)), 0.7)

    def test_total_inertia_mapping_preserves_original_roll_split(self):
        sus = Suspension_A({"cog_total_Ixx_kg_m2": 40.0, "cog_total_Iyy_kg_m2": 103.0,
                            "cog_total_Izz_kg_m2": 128.0})
        np.testing.assert_array_equal(sus.I, [20.0, 20.0, 103.0, 128.0])

    def test_unstable_inertia_is_rejected_instead_of_exporting_finite_garbage(self):
        with self.assertRaises(ValueError):
            workflow.simulate("road_FL_bump", {"cog_total_Ixx_kg_m2": 7.917820044730256})

    def test_design_cases_remain_within_small_angle_and_travel_range(self):
        parameters = dict(ms=260.55, mu_front=14.5, mu_rear=14.3,
                          cog_total_Ixx_kg_m2=41.14105344383404,
                          cog_total_Iyy_kg_m2=103.94191438257367,
                          cog_total_Izz_kg_m2=128.64133384598964,
                          Ks_pitch_N_per_m=141433.7125736544,
                          Ks_roll_N_per_m=100850.59917678294,
                          MR=0.7,
                          hl_rear_heave_spring_ratio=0.8, hl_rear_roll_spring_ratio=0.75,
                          damped_sweep_selected_ratio_used=0.7,
                          hl_front_roll_center_m=0.021, hl_rear_roll_center_m=0.087)
        for scenario in workflow.SCENARIOS:
            data = workflow.simulate(scenario, parameters).result()
            self.assertLess(np.max(np.abs(np.rad2deg(data["theta"][:, :3]))), 5)
            self.assertLess(np.max(np.abs(data["zs"])), 0.1)

    def test_total_inertias_are_hidden_but_remain_upstream_parameters(self):
        from PySide6.QtWidgets import QApplication, QFormLayout, QWidget
        type(self).app = QApplication.instance() or QApplication([])
        host = QWidget()
        plugin = next(item for item in scan_analysis() if item.plugin_id == "full_suspension")
        inertias = {"cog_total_Ixx_kg_m2": "40", "cog_total_Iyy_kg_m2": "103",
                    "cog_total_Izz_kg_m2": "128"}
        context = SimpleNamespace(parameter_form=QFormLayout(host), parameter_edits={},
                                  parameter_values=inertias, output_names=set(inertias),
                                  update_parameter=lambda *_: None)
        MainWindow.build_parameter_fields(context, plugin)
        for name, value in inertias.items():
            self.assertNotIn(name, context.parameter_edits)
            self.assertIn(name, plugin.parameters)
            self.assertIn(name, plugin.hidden_parameters)

    def test_anti_rate_is_shared_with_tender_without_separate_input(self):
        plugins = {item.plugin_id: item for item in scan_analysis()}
        full = plugins["full_suspension"]
        self.assertIn("anti_geometry_ratio", plugins["tender"].parameters)
        self.assertIn("anti_geometry_ratio", full.parameters)
        self.assertIn("anti_geometry_ratio", full.hidden_parameters)
        self.assertNotIn("full_anti_geometry_ratio", full.parameters)
        for ratio in (0.0, 0.2, 1.0):
            sus = Suspension_A({"anti_geometry_ratio": ratio})
            np.testing.assert_array_equal(sus.geometry.anti.get_rate(None), [-ratio, -ratio, ratio, ratio])
        np.testing.assert_array_equal(Suspension_A({"Kt": 80000.0}).geometry.anti.get_rate(None),
                                      Suspension_A().geometry.anti.get_rate(None))

    def test_tender_ratio_uses_two_spring_output_and_orders_its_producer(self):
        plugins = {item.plugin_id: item for item in scan_analysis()}
        full = plugins["full_suspension"]
        name = "tender_to_heave_stiffness_ratio"
        self.assertIn(name, plugins["two_spring"].outputs)
        self.assertIn(name, full.parameters)
        self.assertIn(name, full.hidden_parameters)
        self.assertNotIn("full_heave_tender_ratio", full.parameters)
        self.assertNotIn(name, full.parameter_defaults)
        for ratio in (0.2, 0.5, 0.5187885873759743, 2.0):
            sus = Suspension_A({name: ratio})
            for kc in sus.shock_list[:2]:
                self.assertAlmostEqual(kc.spring.tender / kc.spring.main, ratio)
        with (ROOT / "data/analysis_flow.csv").open(encoding="utf-8-sig", newline="") as stream:
            flow = list(csv.DictReader(stream))
        values = {key: "1" for plugin in plugins.values() for key in plugin.parameters}
        context = SimpleNamespace(flow=flow, plugins_by_id=plugins, parameter_values=values)
        order = [row["node_id"] for row in MainWindow._required_analysis_rows(context, "full_suspension")]
        self.assertLess(order.index("2_spring"), order.index("full_suspension"))

    def test_switch_travel_uses_total_tender_stroke_and_converts_mm_to_m(self):
        plugins = {item.plugin_id: item for item in scan_analysis()}
        full = plugins["full_suspension"]
        name = "tender_bind_total_stroke_mm"
        self.assertIn(name, plugins["tender"].outputs)
        self.assertIn(name, full.parameters)
        self.assertIn(name, full.hidden_parameters)
        self.assertNotIn("full_heave_tender_travel_m", full.parameters)
        for mm in (0, 4.291115317986952, 10):
            sus = Suspension_A({name: mm})
            for kc in sus.shock_list[:2]:
                self.assertAlmostEqual(kc.spring.travel, mm / 1000)
                self.assertEqual(kc.spring.stiffness(-mm / 1000 - 1e-8), kc.spring.main)
                if mm:
                    self.assertLess(kc.spring.stiffness(-mm / 1000 + 1e-8), kc.spring.main)
        with (ROOT / "data/analysis_flow.csv").open(encoding="utf-8-sig", newline="") as stream:
            flow = list(csv.DictReader(stream))
        values = {key: "1" for plugin in plugins.values() for key in plugin.parameters}
        context = SimpleNamespace(flow=flow, plugins_by_id=plugins, parameter_values=values)
        order = [row["node_id"] for row in MainWindow._required_analysis_rows(context, "full_suspension")]
        self.assertLess(order.index("tender"), order.index("full_suspension"))

    def test_single_node_can_load_legacy_cog_snapshot_without_sprung_inertias(self):
        plugins = {item.plugin_id: item for item in scan_analysis()}
        plugin = plugins["full_suspension"]
        with (ROOT / "data/analysis_flow.csv").open(encoding="utf-8-sig", newline="") as stream:
            flow = list(csv.DictReader(stream))
        values = {key: str(value) for item in plugins.values() for key, value in item.parameter_defaults.items()}
        values.update(load_analysis_parameters(ROOT / "data/analysis_parameters.csv"))
        derived = {key for item in plugins.values() for key in item.outputs}
        values = {key: value for key, value in values.items() if key not in derived}
        legacy = dict(ms=260.0, mu_front=14.5, mu_rear=14.3, cog_total_Ixx_kg_m2=40.0,
                      cog_total_Iyy_kg_m2=103.0, cog_total_Izz_kg_m2=128.0,
                      cog_front_axle_x_used_m=0.765, cog_rear_axle_x_used_m=-0.765,
                      cog_total_x_m=0.0, Ks_pitch_N_per_m=80000.0, Ks_roll_N_per_m=50000.0,
                      tender_to_heave_stiffness_ratio=0.52, tender_bind_total_stroke_mm=4.3,
                      hl_front_roll_center_m=0.025, hl_rear_roll_center_m=0.03,
                      damped_sweep_selected_ratio_used=0.7)
        with TemporaryDirectory(dir=ROOT) as temporary:
            for row in flow:
                exported = {key: value for key, value in legacy.items()
                            if key in plugins[row["analysis_id"]].outputs}
                if not exported:
                    continue
                directory = Path(temporary) / row["node_id"]
                directory.mkdir()
                with (directory / "result.csv").open("w", encoding="utf-8-sig", newline="") as stream:
                    writer = csv.writer(stream)
                    writer.writerow(["category", "name", "number"])
                    writer.writerows(("導出量", key, value) for key, value in exported.items())
            context = SimpleNamespace(flow=flow, plugins_by_id=plugins, parameter_values=values)
            with patch("main.RESULTS_DIR", Path(temporary)):
                restored, _ = MainWindow._single_analysis_values(
                    context, next(row for row in flow if row["node_id"] == "full_suspension"))
            parsed = parse_analysis_parameters(restored, plugin.parameters)
            sus = Suspension_A(parsed)
            np.testing.assert_array_equal(sus.I, [20, 20, 103, 128])
            self.assertNotIn("cog_sprung_Iyy_kg_m2", plugin.parameters)


if __name__ == "__main__":
    unittest.main()
