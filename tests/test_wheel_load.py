"""Equilibrium, null-space feasibility and both wheel-load execution entry points."""

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
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PySide6.QtWidgets import QApplication, QTabWidget, QWidget

from analysis_data import load_analysis_parameters, parse_analysis_parameters
from analysis_result import save_analysis_result
from analysis.wheel_load.models import (G, Vehicle, alpha_bounds, four_wheel_load_cg,
                                        four_wheel_load_lsm, wheel_load_null_direction, wheel_load_stiffness)
from analysis.wheel_load.compare_original import original_functions
from analysis.wheel_load.parameters import STAGES, TITLES
from analysis.wheel_load.workflow import validate
from main import MainWindow
from plugin_loader import scan_analysis

ROOT = Path(__file__).resolve().parents[1]


class WheelLoadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plugins = {plugin.plugin_id: plugin for plugin in scan_analysis()}
        cls.inputs = load_analysis_parameters(ROOT / "data" / "analysis_parameters.csv")
        cls.values = dict(cls.inputs, wl_grid_points="9")
        with redirect_stdout(StringIO()):
            for stage in ("cog_movable", "compressed_travel", "aero_stiffness", "frequency_stiffness", "tire_stiffness"):
                plugin = cls.plugins[stage]
                from analysis_result import normalize_result
                result = normalize_result(plugin.run(parse_analysis_parameters(cls.values, plugin.parameters)))
                figure, outputs = result
                cls.values.update({name: str(value) for name, value in outputs.items()})
                result.close()
        with (ROOT / "data" / "analysis_flow.csv").open(encoding="utf-8-sig", newline="") as stream:
            cls.flow = list(csv.DictReader(stream))

    def test_all_models_obey_equilibrium_with_asymmetric_geometry_and_aero(self):
        car = Vehicle(320, .3, 1.53, 1.2, 1.4, .43, 450, .62)
        for ax, ay in ((0, 0), (7, 9), (-8, -6)):
            cg = four_wheel_load_cg(car, ax, ay)
            lsm = four_wheel_load_lsm(car, ax, ay)
            sus = wheel_load_stiffness(car, ax, ay, 70000, 30000, 25000, 45000)
            for values in (cg, lsm, sus):
                np.testing.assert_allclose(car.matrix @ values, car.target(ax, ay), atol=1e-10)
            np.testing.assert_allclose(car.matrix @ (cg-lsm), 0, atol=1e-10)

    def test_pitch_transfer_is_conserved_and_independent_of_heave_ratio(self):
        car = Vehicle(320, .3, 1.53, 1.25, 1.25, .5)
        first = wheel_load_stiffness(car, G, 0, 80000, 20000, 40000, 40000)
        second = wheel_load_stiffness(car, G, 0, 20000, 80000, 40000, 40000)
        np.testing.assert_allclose(first, second)
        self.assertAlmostEqual(first[:2].sum(), car.mass*G/2-car.mass*G*car.height/car.wheelbase)
        corner = four_wheel_load_cg(car, 0, G)
        self.assertGreater(corner[1], corner[0])
        self.assertGreater(corner[3], corner[2])

    def test_alpha_bounds_handle_zero_direction_and_negative_fixed_load(self):
        lower, upper, valid = alpha_bounds(np.ones(4), np.zeros(4))
        self.assertTrue(valid)
        self.assertTrue(np.isneginf(lower) and np.isposinf(upper))
        self.assertFalse(alpha_bounds(np.array([-1, 1, 1, 1]), np.zeros(4))[2])
        lower, upper, valid = alpha_bounds(np.ones(4), np.array([1, -1, -1, 1]))
        self.assertTrue(valid)
        self.assertEqual((lower, upper), (-1, 1))
        for alpha in (lower, (lower+upper)/2, upper):
            self.assertTrue(np.all(1+alpha*np.array([1, -1, -1, 1]) >= 0))
        self.assertFalse(alpha_bounds(np.array([-2, -2]), np.array([1, -1]))[2])

    def test_fixed_null_basis_survives_identical_solvers_and_interval_closes_at_lift_limit(self):
        car = Vehicle(320, .3, 1.53, 1.25, 1.25, .5)
        direction = wheel_load_null_direction(car)
        self.assertGreater(np.linalg.norm(direction), 0)
        np.testing.assert_allclose(car.matrix @ direction, 0, atol=1e-10)
        widths = []
        for lateral_g in (0, 1, 2, 1.25/(2*.3)):
            lsm = four_wheel_load_lsm(car, 0, lateral_g*G)
            cg = four_wheel_load_cg(car, 0, lateral_g*G)
            np.testing.assert_allclose(lsm, cg, atol=1e-10)
            lower, upper, feasible = alpha_bounds(lsm, direction)
            expected = 1-2*lateral_g*car.height/car.front_track
            self.assertTrue(feasible)
            self.assertAlmostEqual(lower, -expected)
            self.assertAlmostEqual(upper, expected)
            for alpha in (lower, upper):
                self.assertGreaterEqual(np.min(lsm+alpha*direction), -1e-9)
            self.assertLess(np.min(lsm+(lower-.01)*direction), 0)
            self.assertLess(np.min(lsm+(upper+.01)*direction), 0)
            widths.append(upper-lower)
        self.assertTrue(np.all(np.diff(widths) < 0))
        self.assertFalse(alpha_bounds(four_wheel_load_lsm(car, 0, 2.2*G), direction)[2])

    def test_fixed_null_basis_covers_asymmetric_tracks_and_axle_loads(self):
        car = Vehicle(320, .3, 1.53, 1.2, 1.4, .43, 450, .62)
        direction = wheel_load_null_direction(car)
        np.testing.assert_allclose(car.matrix @ direction, 0, atol=1e-10)
        for ax, ay in ((0, 0), (G, G), (-G, -G)):
            lsm = four_wheel_load_lsm(car, ax, ay)
            lower, upper, feasible = alpha_bounds(lsm, direction)
            self.assertTrue(feasible)
            for alpha in (lower, upper, (lower+upper)/2):
                loads = lsm+alpha*direction
                self.assertGreaterEqual(np.min(loads), -1e-9)
                np.testing.assert_allclose(car.matrix @ loads, car.target(ax, ay), atol=1e-9)

    @unittest.skipUnless(all((ROOT / "new" / name).is_file() for name in ("FWL_solver.py", "sus_load.py")),
                         "Optional original wheel-load source fixtures are absent from this checkout")
    def test_original_cg_lsm_match_after_lateral_coordinate_conversion(self):
        originals = original_functions(ROOT)
        car = Vehicle(320, .3, 1.53, 1.25, 1.25, .43)
        original_car = SimpleNamespace(m=car.mass, h=car.height, L=car.wheelbase,
                                       d=car.front_track, CG_x=np.array([.43, .57]), CG_y=np.array([.5, .5]))
        for name, solver in (("cg", four_wheel_load_cg), ("lsm", four_wheel_load_lsm)):
            for ax, ay in ((0, 0), (G, G), (-2*G, -G)):
                old = originals[f"four_wheel_load_{name}"](ax, -ay, None, None, original_car)
                np.testing.assert_allclose(old, solver(car, ax, ay), atol=1e-10)

    def test_main_and_independent_diagrams_have_the_same_four_node_chain(self):
        independent = [row for row in self.flow if row["flow_row"] == "tertiary"]
        self.assertEqual([row["node_id"] for row in independent], list(STAGES))
        self.assertEqual(independent[0]["branch_from"], "cog_movable")
        self.assertTrue(all(not row["branch_from"] and not row["merge_from"] for row in independent[1:]))
        for flow in (self.flow, independent):
            captures = []
            window = SimpleNamespace(flow=flow, flow_view=SimpleNamespace(setHtml=captures.append))
            MainWindow.build_flow_buttons(window)
            source = unescape(re.search(r'<div class="mermaid">(.*?)</div>', captures[0], re.S).group(1))
            graph_ids = {row["node_id"]: f"flow_node_{i}" for i, row in enumerate(flow)}
            for first, second in zip(STAGES, STAGES[1:]):
                self.assertIn(f"{graph_ids[first]} --> {graph_ids[second]}", source)
            wheel_ids = {graph_ids[stage] for stage in STAGES}
            edges = re.findall(r"(flow_node_\d+) --> (flow_node_\d+)", source)
            external = {(first, second) for first, second in edges if (first in wheel_ids) != (second in wheel_ids)}
            self.assertEqual(external, {(graph_ids["cog_movable"], graph_ids["FWL"])} if flow is self.flow else set())
            for title in TITLES:
                self.assertIn(title, source)

    def test_selected_wheel_node_resolves_missing_stiffness_and_four_stages(self):
        window = SimpleNamespace(flow=self.flow, plugins_by_id=self.plugins, parameter_values=dict(self.inputs))
        rows = MainWindow._required_analysis_rows(window, "max_load")
        self.assertEqual([row["node_id"] for row in rows], [
            "cog_movable", "compressed_travel", "aero_stiffness", "frequency_stiffness", "tire_stiffness", *STAGES])
        window.parameter_values = self.values
        self.assertEqual([row["node_id"] for row in MainWindow._required_analysis_rows(window, "max_load")], [
            "cog_movable", "compressed_travel", "aero_stiffness", "frequency_stiffness", "tire_stiffness", *STAGES])

    def test_one_flow_view_keeps_wheel_nodes_without_extra_tab_or_run_button(self):
        class FlowPlaceholder(QWidget):
            def setPage(self, page):
                pass

            def settings(self):
                return MagicMock()

            def setHtml(self, source):
                self.source = source

        app = QApplication.instance() or QApplication([])
        with (patch("main.QWebEngineView", side_effect=FlowPlaceholder) as flow_views, patch("main.FlowDiagramPage"),
              patch.object(MainWindow, "select_csv")):
            window = MainWindow()
        try:
            self.assertEqual(flow_views.call_count, 1)
            self.assertFalse(window.findChildren(QTabWidget))
            self.assertFalse(hasattr(window, "run_wheel_load_button"))
            self.assertIn("flow-node://", window.flow_view.source)
            for title in TITLES:
                self.assertIn(title, window.flow_view.source)
            window.handle_flow_node_request("max_load", False)
            self.assertEqual(window.active_node_id, "max_load")
            self.assertEqual(set(window.parameter_edits), {"mu_w", "wl_mu_y"})
            with patch.object(window, "_start_analysis") as start:
                window.run_selected_button.click()
                rows = start.call_args.args[0]
                self.assertEqual([row["node_id"] for row in rows], [
                    "cog_movable", "compressed_travel", "aero_stiffness", "frequency_stiffness", "tire_stiffness", *STAGES])
                window.analysis_runner = object()
                window.run_selected_button.click()
                self.assertEqual(start.call_count, 1)
                window.analysis_runner = None
        finally:
            # Avoid writing the user's last-set CSV from a test window.
            window.deleteLater()
            app.processEvents()

    def test_four_stages_export_plots_tables_notes_and_report(self):
        values = dict(self.values)
        with TemporaryDirectory(dir=ROOT) as temporary, redirect_stdout(StringIO()):
            for stage in STAGES:
                plugin = self.plugins["fwl" if stage == "FWL" else stage]
                parameters = parse_analysis_parameters(values, plugin.parameters)
                result = plugin.run(parameters)
                try:
                    self.assertEqual(set(result.outputs), set(plugin.outputs))
                    self.assertTrue(all(np.isfinite(value) for value in result.outputs.values()))
                    self.assertTrue(result.tables)
                    save_analysis_result(temporary, stage, parameters, result)
                    for name, value in result.outputs.items():
                        values[name] = str(value)
                    destination = Path(temporary) / stage
                    for filename in ("plot.png", "plots.json", "result.csv", "analysis.md"):
                        self.assertTrue((destination / filename).is_file())
                    if stage == "solver_compar":
                        sweep = result.tables["null_space_sweep.csv"]
                        self.assertTrue(np.isfinite(sweep.alpha_min).all())
                        self.assertTrue(np.isfinite(sweep.alpha_max).all())
                        from analysis.wheel_load.workflow import make_vehicle
                        car = make_vehicle(parameters)
                        lower, upper, _ = alpha_bounds(four_wheel_load_lsm(car, 0, 0), wheel_load_null_direction(car))
                        self.assertAlmostEqual(sweep.alpha_min.iloc[0], lower)
                        self.assertAlmostEqual(sweep.alpha_max.iloc[0], upper)
                        self.assertFalse(sweep.feasible.iloc[-1])
                        self.assertGreater(sweep.alpha_min.iloc[-1], sweep.alpha_max.iloc[-1])
                    if stage == "max_load":
                        table = result.tables["tire_force_limits.csv"]
                        np.testing.assert_allclose(table.Fx_limit_N, parameters["mu_w"]*table.Fz_clipped_N)
                        self.assertTrue((table.Fz_clipped_N >= 0).all())
                        self.assertTrue((table.raw_Fz_N < 0).any())
                        self.assertEqual(result.outputs["wl_max_load_contact_valid"], 0)
                finally:
                    result.close()
            report = (Path(temporary) / "wheel_load" / "index.html").read_text(encoding="utf-8")
            for stage in STAGES:
                self.assertIn(f"../{stage}/plot.png", report)

    def test_nonfinite_and_invalid_parameter_ranges_are_rejected(self):
        for values in ({"ms": np.nan}, {"ms": 0}, {"wl_grid_points": 2},
                       {"wl_grid_points": 3.5}, {"wl_aero_front_ratio": 1.1}, {"mu_w": -1}):
            with self.assertRaises(ValueError):
                validate(values)

    def test_scanning_plugins_has_no_plot_side_effects(self):
        before = set(plt.get_fignums())
        scan_analysis()
        self.assertEqual(before, set(plt.get_fignums()))


if __name__ == "__main__":
    unittest.main()
