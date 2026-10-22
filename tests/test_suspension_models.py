"""Per-model scope, shared physical parameters, complete exports and GIF playback."""

import csv
from contextlib import redirect_stdout
from io import BytesIO, StringIO
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from PySide6.QtGui import QMovie
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from analysis.suspension_models.parameters import STAGES, make_suspension, scenarios_for
from app.analysis_data import load_analysis_parameters, parse_analysis_parameters
from app.analysis_result import load_plot_choices, normalize_result, save_analysis_result
from app.flow_diagram import flow_edges
from app.plugin_loader import scan_analysis
from main import MainWindow, ScalableImageLabel
from analysis.suspension_models import batch_cases, batch_runner, data_creator

ROOT = Path(__file__).resolve().parents[1]


class SuspensionModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plugins = {plugin.plugin_id: plugin for plugin in scan_analysis()}
        cls.values = {key: str(value) for plugin in cls.plugins.values()
                      for key, value in plugin.parameter_defaults.items()}
        cls.values.update(load_analysis_parameters(ROOT / "data/analysis_parameters.csv"))
        with (ROOT / "data/analysis_flow.csv").open(encoding="utf-8-sig", newline="") as stream:
            cls.flow = list(csv.DictReader(stream))
        cls.results = {}
        with redirect_stdout(StringIO()):
            for stage in ("cog_movable", "compressed_travel", "aero_stiffness", "frequency_stiffness",
                          "tire_stiffness", "damping_rate", "damped_oscillation_analysis", "overall_rigidity",
                          "roll_center", "roll_center_min_load_f", "roll_center_same_load_r", *STAGES):
                plugin = cls.plugins[stage]
                parameters = parse_analysis_parameters(cls.values, plugin.parameters)
                result = normalize_result(plugin.run(parameters))
                try:
                    cls.values.update({name: str(value) for name, value in result.outputs.items()})
                    if stage in STAGES:
                        cls.results[stage] = result
                finally:
                    result.close()

    def test_flow_has_exactly_three_model_chains_and_unique_click_titles(self):
        expected = set()
        for chain in (
            ("single_spring_model", "one_eighth_suspension_model", "double_spring_model", "quarter_suspension_model"),
            ("two_mass_suspension_2dof_model", "two_mass_suspension_model", "half_suspension_2dof_model_lr",
             "half_suspension_model_lr", "half_rollcenter_all_model"),
            ("half_suspension_2dof_model_fr", "half_suspension_model_fr"),
        ):
            expected.update(zip(("damped_oscillation_analysis", *chain), chain))
        expected.update({
            ("roll_center_same_load_r", "half_suspension_model_lr"),
            ("roll_center_same_load_r", "half_rollcenter_all_model"),
        })
        actual = {(a, b) for a, b in flow_edges(self.flow) if a in STAGES or b in STAGES}
        self.assertEqual(actual, expected)
        self.assertEqual(len({row["title"] for row in self.flow}), len(self.flow))
        self.assertEqual([int(row["order"]) for row in self.flow], list(range(1, len(self.flow) + 1)))

    def test_full_workflow_orders_roll_center_outputs_before_lr_models(self):
        window = SimpleNamespace(flow=self.flow, plugins_by_id=self.plugins, parameter_values=self.values)
        ordered = [row["node_id"] for row in MainWindow._all_analysis_rows_in_dependency_order(window)]
        for stage in ("half_suspension_model_lr", "half_rollcenter_all_model"):
            self.assertLess(ordered.index("roll_center_min_load_f"), ordered.index(stage))
            self.assertLess(ordered.index("roll_center_same_load_r"), ordered.index(stage))
        self.assertEqual(set(ordered), {row["node_id"] for row in self.flow})

    def test_each_model_is_independent_and_exposes_only_manual_settings(self):
        window = SimpleNamespace(flow=self.flow, plugins_by_id=self.plugins, parameter_values=self.values)
        visible_by_family = {
            "quarter": {"Kt", "MR"},
            "LR": {"t", "Kt", "k_frame_to_roll_ratio"},
            "FR": {"Kt", "hl_rear_heave_spring_ratio"},
        }
        for stage in STAGES:
            plugin = self.plugins[stage]
            family = STAGES[stage][0]
            self.assertEqual(set(plugin.parameters) - plugin.hidden_parameters, visible_by_family[family])
            self.assertTrue(visible_by_family[family].issubset(plugin.parameter_defaults))
            if stage in {"half_suspension_model_lr", "half_rollcenter_all_model"}:
                self.assertIn("roll_center_same_load_r", plugin.required_analyses)
                self.assertIn("hl_front_roll_center_m", plugin.parameters)
                self.assertIn("hl_rear_roll_center_m", plugin.parameters)
            dependencies = {row["node_id"] for row in MainWindow._required_analysis_rows(window, stage)}
            self.assertIn("damped_oscillation_analysis", dependencies)
            self.assertEqual(dependencies.intersection(STAGES), {stage})
            ordered = [row["node_id"] for row in MainWindow._required_analysis_rows(window, stage)]
            self.assertLess(ordered.index("damped_oscillation_analysis"), ordered.index(stage))
            if stage in {"half_suspension_model_lr", "half_rollcenter_all_model"}:
                self.assertLess(ordered.index("roll_center_min_load_f"), ordered.index(stage))
                self.assertLess(ordered.index("roll_center_same_load_r"), ordered.index(stage))
            self.assertNotIn("analysis.md", self.results[stage].artifacts)
            self.assertTrue((ROOT / "data/results" / stage / "analysis.md").is_file())
            files = {Path(filename).resolve() for filename in plugin.input_files}
            for name in ("batch_cases.py", "data_creator.py", "batch_runner.py", "Parameter_set/Suspension.py"):
                self.assertIn((ROOT / "analysis/suspension_models" / name).resolve(), files)
            self.assertTrue(all(path.is_relative_to(ROOT / "analysis/suspension_models") for path in files))

    def test_default_suspension_values_are_preserved_without_upstream(self):
        for family, specification in batch_cases.FAMILIES.items():
            self.assertEqual(vars(make_suspension(family, {})), vars(specification.suspension_factory()))

    def test_bundle_runs_with_legacy_imports_blocked(self):
        # A fresh interpreter prevents previously loaded legacy modules from
        # hiding a dependency on new/ during the migration.
        script = '''
import importlib.abc
import sys
class BlockLegacy(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "new" or fullname.startswith("new."):
            raise AssertionError("Legacy dependency: " + fullname)
sys.meta_path.insert(0, BlockLegacy())
from app.plugin_loader import scan_analysis
from analysis.suspension_models import batch_cases, batch_runner
from analysis.suspension_models.parameters import STAGES
plugins = {plugin.plugin_id: plugin for plugin in scan_analysis()}
assert set(STAGES).issubset(plugins)
for family in batch_cases.FAMILIES.values():
    assert family.suspension_factory.__module__.startswith("analysis.suspension_models.")
    assert all(model.function.__module__.startswith("analysis.suspension_models.") for model in family.models.values())
cases, skipped = batch_runner.build_plan(list(batch_cases.FAMILIES))
assert len(cases) == 38
rendered = set()
for case in cases:
    suspension, state, road, model, config = batch_runner.prepare_case(**case)
    logger = batch_runner.simulate_case(suspension, state, road, model, config)
    if case["family"] not in rendered:
        assert batch_runner.save_animation(logger, fps=2, dpi=30).startswith(b"GIF")
        rendered.add(case["family"])
assert len(rendered) == 3
assert not any(name == "new" or name.startswith("new.") for name in sys.modules)
'''
        completed = subprocess.run([sys.executable, "-X", "utf8", "-c", script], cwd=ROOT,
                                   capture_output=True, text=True, encoding="utf-8", timeout=60)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_parameter_conversion_recomputes_dependent_physical_values(self):
        values = dict(ms=280.0, mu=12.0, Ks=35000.0, Kt=95000.0, MR=0.8,
                      damped_sweep_selected_ratio_used=0.5,
                      damped_sweep_selected_coefficient_Ns_per_m=1500.0,
                      t=1.4, h_cog=0.35, cog_total_Ixx_kg_m2=64.0,
                      cog_total_Iyy_kg_m2=100.0, L=1.8)
        for family in batch_cases.FAMILIES:
            suspension = make_suspension(family, values)
            original = batch_cases.FAMILIES[family].suspension_factory()
            self.assertEqual(suspension.ms, 70)
            self.assertEqual(suspension.mu, 12)
            self.assertEqual(suspension.m_corner, 82)
            self.assertEqual(suspension.kt, 95000)
            self.assertEqual(suspension.ct, original.ct)
            if family == "quarter":
                self.assertEqual(suspension.cs, 1500)
                self.assertAlmostEqual(suspension.kw, 22400)
                self.assertAlmostEqual(suspension.ride_rate, 22400 * 95000 / 117400)
            elif family == "LR":
                self.assertEqual(suspension.Ix, 32)
                self.assertEqual(suspension.track, 1.4)
                self.assertEqual(suspension.h_rc, original.h_rc)
                self.assertEqual(suspension.m_frame, 70.0)
                self.assertAlmostEqual(suspension.k_heave, 17500)
                self.assertAlmostEqual(suspension.k_roll, 17500)
                self.assertAlmostEqual(suspension.k_frame / suspension.k_roll, original.k_frame / original.k_roll)
                self.assertAlmostEqual(suspension.c_heave, np.sqrt(17500 * 70))
                self.assertAlmostEqual(suspension.c_roll, np.sqrt(17500 * 2 * 32 / 1.4**2))
            else:
                self.assertEqual(suspension.Iy, 50.0)
                self.assertAlmostEqual(suspension.l, 1.8)
                self.assertAlmostEqual(suspension.lf / suspension.lr, original.lf / original.lr)
                self.assertAlmostEqual(suspension.k_heave_f, 17500)
                self.assertEqual(suspension.anti_dive_front, original.anti_dive_front)
                effective = 1 / (1 / 140 + suspension.lf**2 / suspension.Iy)
                self.assertAlmostEqual(suspension.c_heave_f, np.sqrt(17500 * effective))

    def test_half_car_uses_separate_pitch_roll_and_rear_heave_rates_halved(self):
        values = {
            "ms": 280.0, "mu": 12.0, "Ks": 35000.0,
            "Ks_pitch_N_per_m": 40000.0, "Ks_roll_N_per_m": 24000.0,
            "Kt": 95000.0, "MR": 0.8, "hl_rear_heave_spring_ratio": 0.75,
        }
        quarter = make_suspension("quarter", values)
        lr = make_suspension("LR", values)
        fr = make_suspension("FR", values)
        self.assertEqual(quarter.ks, 35000.0)
        self.assertAlmostEqual(lr.k_heave, 40000 / 2)
        self.assertAlmostEqual(lr.k_roll, 24000 / 2)
        self.assertAlmostEqual(fr.k_heave_f, 40000 / 2)
        self.assertAlmostEqual(fr.k_heave_r, 40000 * 0.75 / 2)

    def test_manual_suspension_geometry_and_tire_inputs_override_defaults(self):
        lr = make_suspension("LR", {
            "ms": 280.0, "t": 1.42, "Kt": 910000.0,
            "cog_total_Ixx_kg_m2": 84.0,
            "k_frame_to_roll_ratio": 8.0,
            "hl_front_roll_center_m": 0.08,
            "hl_rear_roll_center_m": 0.16,
        })
        fr = make_suspension("FR", {
            "L": 1.62, "Kt": 91000.0, "cog_total_Iyy_kg_m2": 124.0,
            "hl_rear_heave_spring_ratio": 0.7, "anti_geometry_ratio": 0.25,
        })
        self.assertEqual((lr.track, lr.kt), (1.42, 910000.0))
        self.assertEqual((lr.h_rc, lr.tau_rc), (0.12, 0.005))
        self.assertEqual(lr.Ix, 42.0)
        self.assertEqual(lr.m_frame, 70.0)
        self.assertEqual(lr.ct, batch_cases.FAMILIES["LR"].suspension_factory().ct)
        self.assertEqual((lr.k_left, lr.k_right), (0.0, 0.0))
        self.assertAlmostEqual(lr.k_frame / lr.k_roll, 8.0)
        self.assertEqual(lr.c_frame, 50.0)
        self.assertEqual((fr.l, fr.kt, fr.Iy), (1.62, 91000.0, 62.0))
        self.assertEqual(fr.ct, batch_cases.FAMILIES["FR"].suspension_factory().ct)
        self.assertEqual((fr.k_front, fr.k_rear), (0.0, 0.0))
        self.assertEqual((fr.anti_dive_front, fr.anti_squat_rear), (0.25, 0.25))
        self.assertAlmostEqual(fr.k_heave_r / fr.k_heave_f, 0.7)

    def test_all_38_cases_have_complete_finite_curves_and_real_animations(self):
        count = 0
        for stage, result in self.results.items():
            with self.subTest(stage=stage):
                family, model, _ = STAGES[stage]
                expected = scenarios_for(stage)
                configs = json.loads(result.artifacts["cases.json"])
                self.assertEqual([config["scenario"] for config in configs], expected)
                self.assertEqual(set(result.outputs), set(self.plugins[stage].outputs))
                self.assertTrue(all(np.isfinite(value) for value in result.outputs.values()))
                self.assertEqual(result.outputs[f"{stage}_case_count"], len(expected))
                for figure in (result.figure, *result.figures.values()):
                    self.assertLessEqual(len(figure.axes), 4)
                    self.assertTrue(all(axis.has_data() for axis in figure.axes))
                for scenario, config in zip(expected, configs):
                    self.assertEqual(config["family"], family)
                    self.assertEqual(config["model"], model)
                    self.assertEqual(config["dt"], batch_cases.DEFAULT_DT)
                    for name, value in batch_cases.FAMILIES[family].scenarios[scenario].parameters.items():
                        self.assertEqual(config["input_parameters"][name], value)
                    self.assertAlmostEqual(config["suspension_parameters"]["ms"], float(self.values["ms"]) / 4)
                    frame = result.tables[f"{scenario}_timeseries.csv"]
                    self.assertTrue(np.isfinite(frame.to_numpy()).all())
                    self.assertEqual(frame.t.iloc[0], 0)
                    self.assertEqual(frame.t.iloc[-1], batch_cases.SIMULATION_TIME)
                    self.assertEqual(len(frame), round(batch_cases.SIMULATION_TIME / batch_cases.DEFAULT_DT) + 1)
                    initial_motion = [name for name in frame if name.endswith(("zs", "zu", "vzs", "vzu"))]
                    self.assertTrue((frame[initial_motion].iloc[0] == 0).all())
                    with Image.open(BytesIO(result.artifacts[f"{scenario}.gif"])) as animation:
                        self.assertEqual(animation.n_frames, max(2, round(batch_cases.SIMULATION_TIME * data_creator.FPS)))
                        self.assertEqual(animation.info["loop"], 0)
                count += len(expected)
        self.assertEqual(count, 38)

    def test_random_seed_comes_from_scenario_and_road_uses_updated_geometry(self):
        condition = batch_cases.FAMILIES["quarter"].scenarios["random"]
        original_seed = condition.parameters["seed"]
        try:
            condition.parameters["seed"] = 17
            first = batch_runner.prepare_case("quarter", "quarter", "random")
            second = batch_runner.prepare_case("quarter", "quarter", "random", seed=0)
            self.assertEqual(first[-1]["input_parameters"]["seed"], 17)
            self.assertEqual(second[-1]["input_parameters"]["seed"], 0)
        finally:
            condition.parameters["seed"] = original_seed
        suspension = make_suspension("FR", {"L": 2.0, "ms": 300.0, "mu": 10.0})
        *_, config = batch_runner.prepare_case("FR", "half", "impulse_drive", suspension=suspension)
        self.assertEqual(config["input_parameters"]["l"], 2.0)
        *_, config = batch_runner.prepare_case("FR", "half", "accelerate", suspension=suspension)
        self.assertEqual(config["input_parameters"]["m"], 170.0)

    def test_export_manifest_gif_playback_and_return_to_static_plot(self):
        app = QApplication.instance() or QApplication([])
        result = self.results["quarter_suspension_model"]
        with TemporaryDirectory(dir=ROOT) as temporary:
            folder = Path(temporary).resolve()
            self.assertTrue(folder.is_relative_to(ROOT))
            save_analysis_result(folder, "quarter_suspension_model", {}, result)
            exported = folder / "quarter_suspension_model"
            choices = load_plot_choices(exported)
            self.assertEqual(len(choices), 9)
            self.assertEqual({name for _, name in choices if name.endswith(".gif")},
                             {f"{name}.gif" for name in scenarios_for("quarter_suspension_model")})
            label = ScalableImageLabel()
            try:
                label.resize(800, 600)
                label.set_image(exported / "step.gif")
                self.assertIsNotNone(label.animation)
                self.assertEqual(label.animation.state(), QMovie.MovieState.Running)
                self.assertFalse(label.original_pixmap.isNull())
                QTest.qWait(160)
                self.assertGreaterEqual(label.animation.currentFrameNumber(), 1)
                label.set_image(exported / "plot.png")
                self.assertIsNone(label.animation)
                self.assertFalse(label.original_pixmap.isNull())
                # PKL export remains readable by the original batch renderer.
                logger = batch_runner.SimulationLogger.load(exported / "step.pkl")
                batch_runner.save_animation(logger, exported / "disk_copy.gif", fps=2, dpi=40)
                self.assertTrue((exported / "disk_copy.gif").is_file())
            finally:
                label.close()
                app.processEvents()


if __name__ == "__main__":
    unittest.main()
