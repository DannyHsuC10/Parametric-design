"""Map interpolation, source integration, and force-limit export checks."""

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import matplotlib
matplotlib.use("Agg")
import numpy as np

from analysis.Pacejka_tire_model.model.api import CalculationInput, MF_Universal_solver, load_tir
from analysis.tire_analysis.mapping_workflow import build_operating_map, run_force_limit
from analysis.tire_analysis.tire_mapping_tool import DEFAULT_OUTPUT, TireForceMap
from analysis.tire_analysis.tire_force_limit import get_fz_slice, solve_fx_limits_at_fy, _iso_fy_candidates
from app.analysis_result import save_analysis_result, load_plot_choices
from app.plugin_loader import scan_analysis
from app.flow_diagram import flow_edges
from main import MainWindow


class TireMappingTests(unittest.TestCase):
    def test_registration_dependencies_and_map_inputs(self):
        plugins = {plugin.plugin_id: plugin for plugin in scan_analysis()}
        flow = MainWindow.load_flow(SimpleNamespace(plugins_by_id=plugins))
        plugin = plugins["tire_maping_force_limit"]
        window = SimpleNamespace(flow=flow, plugins_by_id=plugins, parameter_values=plugin.parameter_defaults)
        required = MainWindow._required_analysis_rows(window, plugin.plugin_id)
        self.assertEqual([row["node_id"] for row in required],
                         ["tire_model", "tire_pressure", "tire_camber", "tire_maping_force_limit"])
        self.assertEqual({edge for edge in flow_edges(flow) if plugin.plugin_id in edge},
                         {("tire_camber", plugin.plugin_id)})
        self.assertIn(DEFAULT_OUTPUT, plugin.input_files)
        self.assertTrue(DEFAULT_OUTPUT.is_file())
        self.assertEqual(set(plugin.parameters), {"tire_pressure_Pa", "tire_camber_deg"})
        self.assertEqual(set(plugin.parameters) - plugin.hidden_parameters, set())

    def test_source_interpolation_and_recomputed_camber_match_model(self):
        source = TireForceMap.load()
        index = 5
        fz = (source.fz_axis[index] + source.fz_axis[index + 1]) / 2
        actual = get_fz_slice(fz=fz)
        np.testing.assert_allclose(actual["FX"], (source.payload["tables"]["FX"][index] +
                                                  source.payload["tables"]["FX"][index + 1]) / 2)
        current = build_operating_map(82319, 3)
        i, j, k = 4, 17, 35
        calc = CalculationInput(FZ=current.fz_axis[i], SA=current.alpha_axis_deg[j],
                                SL=current.kappa_axis[k], IA=3, pressure=82319,
                                V=11.1, Ro=0.203, tir_params=load_tir())
        for key in ("FX", "FY", "MZ"):
            self.assertAlmostEqual(float(current.payload["tables"][key][i, j, k]),
                                   float(np.asarray(MF_Universal_solver(key, calc)).item()))
        self.assertFalse(np.allclose(source.payload["tables"]["FY"], current.payload["tables"]["FY"]))
        for invalid in (0, 8401, float("nan")):
            with self.assertRaises(ValueError):
                get_fz_slice(current, invalid)
        with self.assertRaises(ValueError):
            solve_fx_limits_at_fy(1e9, map_path=current)

    def test_flat_fy_edges_retain_extreme_fx(self):
        grid = {key: np.zeros((2, 2)) for key in ("FX", "FY", "SA_deg", "SL", "MZ", "mu_total")}
        grid["FX"] = np.array([[-7., 9.], [-2., 3.]])
        candidates = _iso_fy_candidates(grid, 0)
        self.assertEqual(min(point["FX"] for point in candidates), -7)
        self.assertEqual(max(point["FX"] for point in candidates), 9)

    def test_real_force_limits_and_gallery_export(self):
        result = run_force_limit({"tire_pressure_Pa": 82319, "tire_camber_deg": 3})
        try:
            boundary = result.tables["fx_fy_boundary.csv"]
            np.testing.assert_allclose(boundary.iloc[0], boundary.iloc[-1])
            self.assertEqual(result.outputs, {})
            axis = result.figure.axes[0]
            self.assertEqual(len(axis.lines), 1)
            self.assertEqual(axis.lines[0].get_color(), "red")
            self.assertEqual(len(axis.collections), 0)
            self.assertEqual(len(axis.texts), 0)
            np.testing.assert_allclose(axis.lines[0].get_xdata(), boundary["FX"])
            np.testing.assert_allclose(axis.lines[0].get_ydata(), boundary["FY"])
            with TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as directory:
                save_analysis_result(directory, "tire_maping_force_limit", {}, result)
                folder = Path(directory) / "tire_maping_force_limit"
                self.assertEqual(len(load_plot_choices(folder)), 1)
                for name in result.tables:
                    self.assertTrue((folder / name).is_file())
        finally:
            result.close()
