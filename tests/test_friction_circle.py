"""Friction-circle registration, source physics, and gallery integration."""

import importlib
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from analysis.Pacejka_tire_model.model.api import CalculationInput, MF_Universal_solver
from analysis.tire_analysis import friction_circle, workflow
from app.analysis_result import load_plot_choices, save_analysis_result
from app.flow_diagram import flow_edges, render_flow_diagram
from app.plugin_loader import scan_analysis
from main import MainWindow

ROOT = Path(__file__).resolve().parents[1]


class FrictionCircleTests(unittest.TestCase):
    def test_node_is_a_model_branch_and_runs_only_its_required_predecessor(self):
        plugins = {item.plugin_id: item for item in scan_analysis()}
        flow = MainWindow.load_flow(SimpleNamespace(plugins_by_id=plugins))
        window = SimpleNamespace(flow=flow, plugins_by_id=plugins, parameter_values={})
        required = MainWindow._required_analysis_rows(window, "friction_circle")
        self.assertEqual([row["node_id"] for row in required], ["tire_model", "friction_circle"])
        self.assertEqual(plugins["friction_circle"].parameters, {})
        self.assertEqual(plugins["friction_circle"].input_files, plugins["tire_model"].input_files)
        self.assertEqual({edge for edge in flow_edges(flow) if "friction_circle" in edge},
                         {("tire_model", "friction_circle")})
        self.assertIn("friction_circle", render_flow_diagram(flow, "輪胎分析"))

    def test_two_surfaces_use_model_defaults_and_export_to_the_gallery(self):
        with patch.object(friction_circle, "MF_Universal_solver", wraps=MF_Universal_solver) as solver:
            result = workflow.run_friction_circle({})
        try:
            self.assertEqual(result.outputs, {"friction_circle_figure_count": 2})
            self.assertEqual(len(result.figures), 2)
            for call in solver.call_args_list:
                direction, calc = call.args
                self.assertEqual(calc.pressure, 82319)
                self.assertEqual(calc.IA, 0)
                actual = MF_Universal_solver(direction, calc)
                self.assertEqual(actual.shape, (50, 50))
                self.assertTrue(np.isfinite(actual).all())
                # Compare a representative grid point with the source's scalar calculation.
                scalar = CalculationInput(
                    FZ=np.broadcast_to(calc.FZ, actual.shape)[31, 17],
                    SA=np.broadcast_to(calc.SA, actual.shape)[31, 17],
                    SL=np.broadcast_to(calc.SL, actual.shape)[31, 17], IA=0, V=10,
                    pressure=82319, tir_params=calc.tir_params)
                self.assertAlmostEqual(actual[31, 17], float(MF_Universal_solver(direction, scalar)))
            fixed_load = solver.call_args_list[0].args[1]
            self.assertEqual(fixed_load.FZ, 800)
            np.testing.assert_allclose([fixed_load.SA.min(), fixed_load.SA.max()], [-10, 10])
            np.testing.assert_allclose([fixed_load.SL.min(), fixed_load.SL.max()], [-0.25, 0.25])
            variable_load = solver.call_args_list[2].args[1]
            self.assertEqual(variable_load.SL, 0.1)
            np.testing.assert_allclose([variable_load.FZ.min(), variable_load.FZ.max()], [0, 1400])
            with TemporaryDirectory(dir=ROOT) as folder:
                save_analysis_result(folder, "friction_circle", {}, result)
                choices = load_plot_choices(Path(folder) / "friction_circle")
                self.assertEqual({file for _, file in choices}, {"plot.png", *result.figures})
        finally:
            result.close()

    def test_import_has_no_plotting_or_file_side_effects(self):
        before = set(plt.get_fignums())
        with patch.object(plt, "show") as show, patch.object(plt.Figure, "savefig") as save:
            importlib.reload(friction_circle)
            importlib.reload(importlib.import_module("analysis.Friction_circle"))
        self.assertEqual(set(plt.get_fignums()), before)
        show.assert_not_called()
        save.assert_not_called()
