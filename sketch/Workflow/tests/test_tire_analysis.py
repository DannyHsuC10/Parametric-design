"""Tire physics, chart exports, and the dependencies of the requested branches."""

from contextlib import chdir, redirect_stdout
import csv
from html import unescape
import importlib
from io import StringIO
import json
import os
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PySide6.QtWidgets import QApplication, QFormLayout, QWidget

from analysis.Pacejka_tire_model import MF_tester
from analysis.Pacejka_tire_model.model.api import CalculationInput, MF_Universal_solver, TIRE_FILE, load_tir
from analysis.tire_analysis.models import (CAMBERS_DEG, LOADS_N, PRESSURES_PSI, PSI_TO_PA,
                                         force_surface, friction_peaks, optimize_lateral)
from app.analysis_data import load_analysis_parameters, parse_analysis_parameters
from app.analysis_result import load_plot_choices, normalize_result, save_analysis_result
from main import MainWindow
from app.plugin_loader import scan_analysis

ROOT = Path(__file__).resolve().parents[1]
STAGES = ("tire_model", "tire_pressure", "tire_camber", "coefficient_of_friction")


class TireAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plugins = {item.plugin_id: item for item in scan_analysis()}
        cls.values = load_analysis_parameters(ROOT / "data/analysis_parameters.csv")
        cls.flow = MainWindow.load_flow(SimpleNamespace(plugins_by_id=cls.plugins))
        cls.params = load_tir()

    def test_tir_file_is_fixed_in_shared_input_data(self):
        self.assertEqual(TIRE_FILE, ROOT / "data/input_data/tire.tir")
        self.assertTrue(TIRE_FILE.is_file())
        self.assertFalse((ROOT / "analysis/Pacejka_tire_model/tir/tire.tir").exists())
        with TemporaryDirectory(dir=ROOT) as folder, chdir(folder):
            self.assertEqual(load_tir(), self.params)
        for plugin in self.plugins.values():
            self.assertNotIn("tire_tir_file", plugin.parameters)
            self.assertNotIn("tire_tir_file", plugin.parameter_defaults)
        for filename in ("analysis_parameters.csv", "analysis_parameters_last_set.csv"):
            self.assertNotIn("tire_tir_file", load_analysis_parameters(ROOT / "data" / filename))

    def test_derived_tire_inputs_are_hidden_but_remain_execution_dependencies(self):
        app = QApplication.instance() or QApplication([])
        host = QWidget()
        window = SimpleNamespace(parameter_form=QFormLayout(host), parameter_edits={},
                                 parameter_values=dict(self.values),
                                 output_names={name for plugin in self.plugins.values() for name in plugin.outputs},
                                 update_parameter=lambda *args: None)
        hidden_friction = {"mu_w", "wl_mu_y"}
        try:
            for plugin in self.plugins.values():
                MainWindow.build_parameter_fields(window, plugin)
                self.assertFalse(hidden_friction.intersection(window.parameter_edits), plugin.plugin_id)
                self.assertNotIn("tire_tir_file", window.parameter_edits)
                if plugin.plugin_id in {*STAGES, "track_analysis"}:
                    self.assertFalse(window.parameter_edits, plugin.plugin_id)
            self.assertEqual(self.plugins["tire_camber"].parameters, {"tire_pressure_Pa": "float"})
            self.assertEqual(self.plugins["coefficient_of_friction"].parameters,
                             {"tire_pressure_Pa": "float", "tire_camber_deg": "float"})
            for plugin in self.plugins.values():
                if hidden_friction.intersection(plugin.parameters):
                    selected = next(row["node_id"] for row in self.flow if row["analysis_id"] == plugin.plugin_id)
                    rows = MainWindow._required_analysis_rows(
                        SimpleNamespace(flow=self.flow, plugins_by_id=self.plugins, parameter_values=self.values), selected)
                    self.assertEqual([row["node_id"] for row in rows[:4]], list(STAGES))
        finally:
            host.close()

    def test_imports_are_quiet_and_do_not_generate_figures_or_write_files(self):
        before = set(plt.get_fignums())
        with redirect_stdout(StringIO()) as printed, patch.object(plt, "show") as show, patch.object(plt.Figure, "savefig") as save:
            for name in ("Pacejka_tire_model.MF_tester", "tire_analysis.models", "tire_analysis.workflow",
                         "Tire_model", "Tire_pressure", "Tire_camber", "Coefficient_of_friction"):
                importlib.reload(importlib.import_module("analysis." + name))
        self.assertEqual(printed.getvalue(), "")
        self.assertEqual(set(plt.get_fignums()), before)
        show.assert_not_called()
        save.assert_not_called()

    def test_requested_graph_edges_and_dependencies_recompute_stale_values(self):
        captures = []
        window = SimpleNamespace(flow=self.flow, plugins_by_id=self.plugins,
                                 parameter_values=self.values | {"tire_pressure_Pa": "1", "tire_camber_deg": "99",
                                                                  "mu_w": "99", "wl_mu_y": "99"},
                                 flow_view=SimpleNamespace(setHtml=captures.append))
        MainWindow.build_flow_buttons(window)
        source = unescape(re.search(r'<div class="mermaid">(.*?)</div>', captures[0], re.S).group(1))
        names = {f"flow_node_{i}": row["node_id"] for i, row in enumerate(self.flow)}
        edges = {(names[a], names[b]) for a, b in re.findall(r"(flow_node_\d+) --> (flow_node_\d+)", source)}
        self.assertEqual([row["node_id"] for row in self.flow[:4]], list(STAGES))
        self.assertTrue(set(zip(STAGES, STAGES[1:])).issubset(edges))
        self.assertEqual({target for first, target in edges if first == STAGES[-1]},
                         {"track_analysis", "skidpad_test", "FWL"})
        self.assertIn(("cog_movable", "FWL"), edges)
        for target in ("track_analysis", "skidpad_test", "FWL", "max_load"):
            required = MainWindow._required_analysis_rows(window, target)
            ids = [row["node_id"] for row in required]
            self.assertEqual(ids[:4], list(STAGES))
            self.assertEqual(ids[-1], target)
        for selected in self.flow:
            # Every selected analysis is acyclic, and dependencies precede uses.
            rows = MainWindow._required_analysis_rows(window, selected["node_id"])
            available = set(self.values) - {key for plugin in self.plugins.values() for key in plugin.outputs}
            for row in rows:
                plugin = self.plugins[row["analysis_id"]]
                self.assertFalse(set(plugin.parameters) - available, row["node_id"])
                available.update(plugin.outputs)

    def test_vectorized_model_matches_original_scalar_formulas(self):
        from new.Pacejka_tire_model.model import api as original
        for out in MF_tester.OUTPUTS:
            for fix in MF_tester.FIX_CASES:
                _, _, _, xs, ys = MF_tester.fig_set(fix, out)
                X, Y = np.meshgrid(xs[[0, 14, 27, 49]], ys[[0, 12, 25, 49]])
                calc = MF_tester.MF_set(slice(None), slice(None), X, Y, fix, self.params)
                actual = np.broadcast_to(MF_Universal_solver(out, calc), X.shape)
                expected = np.empty_like(X)
                for i, j in np.ndindex(X.shape):
                    local = MF_tester.MF_set(i, j, X, Y, fix, self.params)
                    source = original.CalculationInput(FZ=local.FZ, SA=local.SA, SL=local.SL,
                                                       IA=local.IA, pressure=local.pressure,
                                                       tir_params=self.params)
                    expected[i, j] = original.MF_Universal_solver(out, source)
                self.assertTrue(np.all(np.isfinite(actual)), (out, fix))
                np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-12)

    def test_optimizer_matches_rms_objective_and_uses_best_pressure_for_camber(self):
        pressure_index, pressure_rms, surfaces = optimize_lateral(self.params, PRESSURES_PSI)
        expected = [np.sqrt(np.mean(surface**2)) for surface in surfaces]
        np.testing.assert_allclose(pressure_rms, expected)
        self.assertEqual(pressure_index, int(np.argmax(expected)))
        pressure = PRESSURES_PSI[pressure_index] * PSI_TO_PA
        camber_index, camber_rms, surfaces = optimize_lateral(self.params, CAMBERS_DEG, pressure=pressure)
        self.assertEqual(camber_index, int(np.argmax(camber_rms)))
        expected_surface = force_surface(self.params, "FY", np.linspace(-10, 10, 61), LOADS_N,
                                         pressure, CAMBERS_DEG[camber_index])
        np.testing.assert_allclose(surfaces[camber_index], expected_surface)
        calc = CalculationInput(FZ=LOADS_N[30], SA=10, SL=0, IA=CAMBERS_DEG[camber_index],
                                pressure=pressure, tir_params=self.params)
        self.assertAlmostEqual(float(surfaces[camber_index, 30, -1]), MF_Universal_solver("FY", calc))

    def test_regression_excludes_zero_load_and_returns_distinct_directional_coefficients(self):
        for direction, data in friction_peaks(self.params, 8 * PSI_TO_PA, 0).items():
            loads, forces = LOADS_N[1:], data["peak"][1:]
            independent_fit = np.linalg.lstsq(loads[:, None], forces, rcond=None)[0][0]
            self.assertAlmostEqual(data["coefficient"], independent_fit)
            self.assertAlmostEqual(data["peak_mu"], np.max(forces / loads))
            self.assertTrue(np.isfinite(data["mu_curve"]).all(), direction)
            self.assertGreater(data["coefficient"], 0)
        for pressure, camber in ((0, 0), (-1, 0), (np.nan, 0), (1, np.inf)):
            with self.assertRaises(ValueError):
                friction_peaks(self.params, pressure, camber)

    def test_all_source_model_charts_export_and_friction_outputs_reach_consumers(self):
        expected_files = {path.name for path in (ROOT / "new/Pacejka_tire_model/Figures").glob("*.png")}
        self.assertEqual(len(expected_files), 19)
        values = dict(self.values)
        unrelated, _ = plt.subplots()
        try:
            with TemporaryDirectory(dir=ROOT) as folder, redirect_stdout(StringIO()):
                for stage in STAGES:
                    plugin = self.plugins[stage]
                    parameters = parse_analysis_parameters(values, plugin.parameters)
                    result = plugin.run(parameters)
                    try:
                        self.assertEqual(set(result.outputs), set(plugin.outputs))
                        self.assertTrue(all(np.isfinite(value) for value in result.outputs.values()))
                        if stage == "tire_model":
                            self.assertEqual(set(result.figures), expected_files)
                            self.assertEqual(result.outputs["tire_model_figure_count"], 19)
                        save_analysis_result(folder, stage, parameters, result)
                        self.assertEqual(len(load_plot_choices(Path(folder) / stage)), 1 + len(result.figures))
                        values.update({name: str(value) for name, value in result.outputs.items()})
                        if stage == "coefficient_of_friction":
                            saved = json.loads((Path(folder) / stage / "tire.json").read_text(encoding="utf-8"))
                            self.assertEqual(saved["mu_w"], result.outputs["mu_x_RL"])
                            self.assertEqual(saved["wl_mu_y"], result.outputs["mu_y_RL"])
                    finally:
                        result.close()
                self.assertIn(unrelated.number, plt.get_fignums())
                self.assertEqual(float(values["mu_w"]), float(values["mu_x_RL"]))
                self.assertEqual(float(values["wl_mu_y"]), float(values["mu_y_RL"]))
                self.assertNotAlmostEqual(float(values["mu_w"]), float(values["wl_mu_y"]))
                for stage in ("track_analysis", "skidpad_test", "speed_vs_r", "donwforce_target"):
                    self.assertIn("wl_mu_y", self.plugins[stage].parameters)
                    self.assertNotIn("mu_w", self.plugins[stage].parameters)
        finally:
            plt.close(unrelated)
