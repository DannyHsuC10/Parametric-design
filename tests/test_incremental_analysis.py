"""Incremental runs follow actual values, reuse saved work, and recover from failure."""

import csv
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from matplotlib.figure import Figure

from analysis_cache import input_file_state, reusable_outputs
from analysis_data import load_analysis_parameters
from analysis_result import AnalysisResult
from analysis_runner import AnalysisRunner
from plugin_loader import AnalysisPlugin, scan_analysis

ROOT = Path(__file__).resolve().parents[1]


def make_plugin(name, parameters, output, function, *, files=()):
    return AnalysisPlugin(name, SimpleNamespace(
        PLUGIN_ID=name, PARAMETERS=parameters, OUTPUTS={output: output}, INPUT_FILES=files,
        main=Mock(side_effect=lambda p: AnalysisResult(Figure(), {output: function(p)})),
    ))


def export_result(results_dir, node_id, parameters, result):
    """Avoid rendering charts; retain the real input/output export and cache IO."""
    folder = Path(results_dir) / node_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "plot.png").write_bytes(b"chart")
    with (folder / "result.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["category", "name", "number"])
        writer.writerows(("輸入量", key, value) for key, value in parameters.items())
        writer.writerows(("導出量", key, value) for key, value in result.outputs.items())


class IncrementalAnalysisTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(dir=ROOT)
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name).resolve()
        self.assertTrue(self.folder.is_relative_to(ROOT))
        self.execution = []
        self.logs = []
        self.saver = patch("analysis_runner.save_analysis_result", side_effect=export_result).start()
        self.addCleanup(patch.stopall)

    def run_nodes(self, plugins, values, *, selected=None, incremental=True, expect_error=False, rows=None):
        if rows is None:
            rows = [dict(node_id=p.plugin_id, analysis_id=p.plugin_id, title=p.plugin_id) for p in plugins]
        runner = AnalysisRunner({p.plugin_id: p for p in plugins}, rows, values, self.folder,
                                selected_node_id=selected, incremental=incremental)
        self.execution = []
        self.logs = []
        runner.stageStarted.connect(lambda position, total, title: self.execution.append(title))
        runner.log.connect(self.logs.append)
        runner.run()
        if not expect_error:
            self.assertIsNone(runner.error)
        return runner

    def test_motor_change_updates_both_branches_and_skips_unrelated_intermediate_node(self):
        plugins = [
            make_plugin("Tire", {}, "mu", lambda p: 1.6),
            make_plugin("Wheel", {"mu": "float"}, "load", lambda p: p["mu"] * 100),
            make_plugin("Gear", {"torque": "float", "load": "float"}, "ratio", lambda p: p["load"] / p["torque"]),
            make_plugin("Check", {"teeth": "int"}, "valid", lambda p: p["teeth"] > 0),
            make_plugin("Output", {"ratio": "float", "torque": "float"}, "speed", lambda p: p["ratio"] * 20),
            make_plugin("OtherBranch", {"torque": "float"}, "strength", lambda p: p["torque"] * 2),
        ]
        # Sequence alone does not make Check's result depend on Gear's output.
        plugins[3].required_analyses = ("Gear",)
        first = self.run_nodes(plugins, {"torque": "20", "teeth": "21"})
        self.assertEqual(first.completed_count, 6)
        second = self.run_nodes(plugins, {"torque": "40", "teeth": "21"})
        self.assertEqual(self.execution, ["Gear", "Output", "OtherBranch"])
        self.assertEqual((second.completed_count, second.reused_count), (3, 3))
        self.assertEqual(second.values["speed"], "80.0")
        third = self.run_nodes(plugins, {"torque": "40.000", "teeth": "21"})
        self.assertEqual((third.completed_count, third.reused_count), (0, 6))
        self.assertEqual(self.execution, [])

    def test_changed_source_with_same_output_does_not_recalculate_consumer(self):
        plugins = [make_plugin("Source", {"input": "float"}, "derived", lambda p: round(p["input"])),
                   make_plugin("Consumer", {"derived": "float"}, "answer", lambda p: p["derived"] * 2)]
        self.run_nodes(plugins, {"input": "2.1"})
        runner = self.run_nodes(plugins, {"input": "2.2", "derived": "999"})
        self.assertEqual(self.execution, ["Source"])
        self.assertEqual((runner.completed_count, runner.reused_count), (1, 1))
        self.assertEqual(runner.values["answer"], "4.0")

    def test_selected_is_forced_while_valid_upstream_is_reused_and_full_run_forces_all(self):
        plugins = [make_plugin("Source", {}, "derived", lambda p: 3),
                   make_plugin("Selected", {"derived": "float", "gain": "float"}, "answer",
                               lambda p: p["derived"] * p["gain"])]
        self.run_nodes(plugins, {"gain": "2"})
        self.run_nodes(plugins, {"gain": "4"}, selected="Selected")
        self.assertEqual(self.execution, ["Selected"])
        self.run_nodes(plugins, {"gain": "4"}, selected="Selected")
        self.assertEqual(self.execution, ["Selected"])
        self.run_nodes(plugins, {"gain": "4"}, incremental=False)
        self.assertEqual(self.execution, ["Source", "Selected"])

    def test_file_content_change_is_detected_even_when_timestamp_and_size_match(self):
        source = self.folder / "input.xlsx"
        source.write_bytes(b"old")
        plugins = [make_plugin("File", {}, "size", lambda p: source.read_text(), files=(source,)),
                   make_plugin("Consumer", {"size": "str"}, "answer", lambda p: p["size"])]
        self.run_nodes(plugins, {})
        stamp = source.stat()
        source.write_bytes(b"new")
        os.utime(source, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
        runner = self.run_nodes(plugins, {})
        self.assertEqual(self.execution, ["File", "Consumer"])
        self.assertEqual(runner.values["answer"], "new")
        self.run_nodes(plugins, {})
        self.assertEqual(self.execution, [])

    def test_legacy_export_is_adopted_but_newer_source_requires_recalculation(self):
        source = self.folder / "input.csv"
        source.write_text("old", encoding="utf-8")
        plugins = [make_plugin("Legacy", {"input": "float"}, "answer", lambda p: p["input"] * 2,
                               files=(source,))]
        row = dict(node_id="Legacy", analysis_id="Legacy", title="Legacy")
        export_result(self.folder, "Legacy", {"input": 2.0}, AnalysisResult(None, {"answer": 4}))
        result_path = self.folder / "Legacy" / "result.csv"
        old = result_path.stat().st_mtime_ns - 1_000_000
        os.utime(source, ns=(old, old))
        self.run_nodes(plugins, {"input": "2"})
        self.assertEqual(self.execution, [])
        self.assertTrue((self.folder / "Legacy" / "cache.json").is_file())
        self.assertEqual(reusable_outputs(self.folder, row, plugins[0], {"input": 2.0},
                                          input_file_state(plugins[0])), {"answer": "4"})
        (self.folder / "Legacy" / "cache.json").unlink()
        newer = result_path.stat().st_mtime_ns + 1_000_000
        os.utime(source, ns=(newer, newer))
        self.run_nodes(plugins, {"input": "2"})
        self.assertEqual(self.execution, ["Legacy"])

    def test_partial_save_failure_does_not_create_reusable_result_and_retry_resumes(self):
        plugins = [make_plugin("First", {}, "x", lambda p: 1),
                   make_plugin("Failed", {"x": "float"}, "y", lambda p: p["x"] * 2),
                   make_plugin("Last", {"y": "float"}, "z", lambda p: p["y"] * 2)]

        def fail_after_export(results_dir, node_id, parameters, result):
            export_result(results_dir, node_id, parameters, result)
            if node_id == "Failed":
                raise ValueError("failed after writing result.csv")

        self.saver.side_effect = fail_after_export
        failed = self.run_nodes(plugins, {}, expect_error=True)
        self.assertIn("failed after writing result.csv", failed.error)
        self.assertEqual(self.execution, ["First", "Failed"])
        self.saver.side_effect = export_result
        retry = self.run_nodes(plugins, {})
        self.assertEqual(self.execution, ["Failed", "Last"])
        self.assertEqual((retry.completed_count, retry.reused_count), (2, 1))

    def test_missing_and_corrupt_results_are_recalculated(self):
        plugins = [make_plugin("Source", {}, "x", lambda p: 1)]
        self.run_nodes(plugins, {})
        folder = self.folder / "Source"
        for filename, content in (("cache.json", "broken"), ("result.csv", "broken"), ("plot.png", None)):
            with self.subTest(filename=filename):
                if content is None:
                    (folder / filename).unlink()
                else:
                    (folder / filename).write_text(content, encoding="utf-8")
                self.run_nodes(plugins, {})
                self.assertEqual(self.execution, ["Source"])

    def test_real_plugins_declare_their_fixed_data_sources(self):
        plugins = {p.plugin_id: p for p in scan_analysis()}
        for name in ("tire_model", "tire_pressure", "tire_camber", "coefficient_of_friction",
                     "cog_movable", "track_analysis", "psd", "brake_hydraulic_pressure", "motor"):
            with self.subTest(plugin=name):
                files = input_file_state(plugins[name])
                self.assertTrue(files)
                self.assertTrue(all(files.values()))

    def test_real_flow_motor_curve_change_only_invalidates_motor_and_five_gearing_analyses(self):
        plugins = scan_analysis()
        curve = self.folder / "motor.csv"
        curve.write_text("20", encoding="utf-8")
        next(p for p in plugins if p.plugin_id == "motor").input_files = (curve,)
        with (ROOT / "data" / "analysis_flow.csv").open(encoding="utf-8-sig", newline="") as stream:
            flow = list(csv.DictReader(stream))
        values = ({key: str(value) for p in plugins for key, value in p.parameter_defaults.items()}
                  | load_analysis_parameters(ROOT / "data" / "analysis_parameters.csv"))
        for plugin in plugins:
            def analyze(parameters, plugin=plugin):
                outputs = dict.fromkeys(plugin.outputs, 1)
                if plugin.plugin_id == "motor":
                    outputs["drive_motor_torque_Nm"] = float(curve.read_text(encoding="utf-8"))
                if plugin.plugin_id == "gear_rate":
                    outputs["gear_ratio_avg"] = parameters["drive_motor_torque_Nm"] / 10
                return AnalysisResult(Figure(), outputs)
            self.enterContext(patch.object(plugin.module, "main", side_effect=analyze))
        initial = self.run_nodes(plugins, values, rows=flow)
        self.assertEqual(initial.completed_count, len(flow))
        curve.write_text("21", encoding="utf-8")
        changed = self.run_nodes(plugins, values, rows=flow)
        affected = {"motor", "gear_rate", "gear_tooth", "output_check", "acc_resis", "tooth_strength"}
        self.assertEqual(self.execution, [r["title"] for r in flow if r["analysis_id"] in affected])
        self.assertEqual((changed.completed_count, changed.reused_count), (6, len(flow) - 6))


if __name__ == "__main__":
    unittest.main()
