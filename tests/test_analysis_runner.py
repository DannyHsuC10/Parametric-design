"""Progress is visible before the next analysis finishes, with a live Qt event loop."""

from contextlib import ExitStack
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from threading import Event
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import matplotlib.pyplot as plt
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication, QWidget

from app.analysis_runner import AnalysisRunner, LogStream
from app.analysis_settings import NodeSettings, load_node_settings
from main import MainWindow
from app.plugin_loader import AnalysisPlugin

ROOT = Path(__file__).resolve().parents[1]


class FlowPlaceholder(QWidget):
    def setPage(self, page):
        pass

    def settings(self):
        return MagicMock()

    def setHtml(self, html):
        self.html = html


def plugin(name, function, parameters=None, outputs=None):
    return AnalysisPlugin(name, SimpleNamespace(
        PLUGIN_ID=name, TITLE=name, PARAMETERS=parameters or {}, OUTPUTS=outputs or {}, main=function,
    ))


def response(outputs):
    figure, axis = plt.subplots(figsize=(3, 2))
    axis.plot([0, 1], [0, 1])
    return figure, outputs


class AnalysisRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def wait_for(self, predicate, timeout=5):
        if predicate():
            return
        loop = QEventLoop()
        poll = QTimer(loop)
        poll.setInterval(10)
        poll.timeout.connect(lambda: loop.quit() if predicate() else None)
        deadline = QTimer(loop)
        deadline.setSingleShot(True)
        deadline.timeout.connect(loop.quit)
        poll.start()
        deadline.start(int(timeout * 1000))
        loop.exec()
        self.assertTrue(predicate(), "Timed out waiting for background analysis")

    def make_window(self, stack, destination, plugins):
        rows = [dict(order=str(index), node_id=item.plugin_id, title=item.title,
                     analysis_id=item.plugin_id, flow_row="main", branch_from="", merge_from="", flow_group="")
                for index, item in enumerate(plugins, start=1)]
        stack.enter_context(patch("main.QWebEngineView", FlowPlaceholder))
        stack.enter_context(patch("main.FlowDiagramPage"))
        stack.enter_context(patch("main.scan_analysis", return_value=plugins))
        stack.enter_context(patch.object(MainWindow, "load_flow", return_value=rows))
        stack.enter_context(patch.object(MainWindow, "select_csv"))
        stack.enter_context(patch("main.RESULTS_DIR", destination))
        stack.enter_context(patch("main.LAST_SET_CSV", destination / "last.csv"))
        window = MainWindow()
        window.parameter_values = {}
        window.active_node_id = plugins[-1].plugin_id
        return window

    def test_completed_stage_is_visible_while_next_stage_is_running(self):
        gate = Event()
        original_stdout = sys.stdout

        def first(parameters):
            print("first analysis output", flush=True)
            return response({"first_value": 2.0})

        def second(parameters):
            self.assertEqual(parameters["first_value"], 2.0)
            print("second analysis is running", flush=True)
            if not gate.wait(5):
                raise RuntimeError("Test gate timed out")
            return response({"second_value": 4.0})

        plugins = [plugin("First", first, outputs={"first_value": "first output"}),
                   plugin("Second", second, parameters={"first_value": "float"},
                          outputs={"second_value": "second output"})]
        with TemporaryDirectory(dir=ROOT) as temporary, ExitStack() as stack:
            destination = Path(temporary).resolve()
            self.assertTrue(destination.is_relative_to(ROOT.resolve()))
            window = self.make_window(stack, destination, plugins)
            beats = []
            heartbeat = QTimer()
            heartbeat.setInterval(10)
            heartbeat.timeout.connect(lambda: beats.append(True))
            heartbeat.start()
            try:
                window.run_flow()
                runner = window.analysis_runner
                self.assertIsNotNone(runner)
                self.wait_for(lambda: "second analysis is running" in window.console.toPlainText())
                self.assertTrue(runner.isRunning())
                text = window.console.toPlainText()
                self.assertIn("[1/2] 完成：First", text)
                self.assertIn("結果已儲存", text)
                self.assertIn("first analysis output", text)
                self.assertTrue((destination / "First" / "plot.png").exists())
                self.assertEqual(window.parameter_values["first_value"], "2.0")
                self.assertNotIn("second_value", window.parameter_values)
                self.assertFalse(window.run_button.isEnabled())
                self.assertFalse(window.run_affected_button.isEnabled())
                self.assertFalse(window.csv_button.isEnabled())
                self.assertFalse(window.parameter_scroll.isEnabled())
                window.run_flow()
                self.assertIs(window.analysis_runner, runner)
                previous_status = window.status_label.text()
                loop = QEventLoop()
                QTimer.singleShot(300, loop.quit)
                loop.exec()
                self.assertGreater(len(beats), 2)
                self.assertNotEqual(window.status_label.text(), previous_status)
                self.assertIn("Second", window.status_label.text())
                gate.set()
                self.wait_for(lambda: window.analysis_runner is None)
                self.assertIn("[2/2] 完成：Second", window.console.toPlainText())
                self.assertIn("全部完成：2/2", window.console.toPlainText())
                self.assertEqual(window.output_values["second_value"], 4.0)
                self.assertTrue((destination / "Second" / "result.csv").exists())
                self.assertTrue(window.run_button.isEnabled())
                self.assertTrue(window.run_affected_button.isEnabled())
                self.assertTrue(window.parameter_scroll.isEnabled())
                self.assertIs(sys.stdout, original_stdout)
            finally:
                gate.set()
                if window.analysis_runner is not None:
                    window.analysis_runner.wait(5000)
                    self.app.processEvents()
                heartbeat.stop()
                window.close()

    def test_selected_analysis_keeps_dependency_logs_and_output_order(self):
        plugins = [plugin("Source", lambda parameters: response({"source_value": 3}),
                          outputs={"source_value": "value"}),
                   plugin("Selected", lambda parameters: response({"answer": parameters["source_value"] * 2}),
                          parameters={"source_value": "float"}, outputs={"answer": "answer"})]
        with TemporaryDirectory(dir=ROOT) as temporary, ExitStack() as stack:
            destination = Path(temporary).resolve()
            self.assertTrue(destination.is_relative_to(ROOT.resolve()))
            window = self.make_window(stack, destination, plugins)
            try:
                window.parameter_values["source_value"] = "999"
                window.run_selected_with_dependencies()
                self.wait_for(lambda: window.analysis_runner is None)
                text = window.console.toPlainText()
                self.assertIn("必要前置分析｜Source", text)
                self.assertIn("所選分析｜Selected", text)
                self.assertEqual(window.output_values["answer"], 6)
            finally:
                if window.analysis_runner is not None:
                    window.analysis_runner.wait(5000)
                    self.app.processEvents()
                window.close()

    def test_single_analysis_reuses_upstream_after_edit_without_running_source(self):
        source = MagicMock(return_value=None)
        source.side_effect = lambda parameters: response({"source_value": 3})
        plugins = [plugin("Source", source, outputs={"source_value": "value"}),
                   plugin("Selected", lambda p: response({"answer": p["source_value"] * p["gain"]}),
                          parameters={"source_value": "float", "gain": "float"}, outputs={"answer": "answer"})]
        with TemporaryDirectory(dir=ROOT) as temporary, ExitStack() as stack:
            window = self.make_window(stack, Path(temporary), plugins)
            try:
                window.parameter_values["gain"] = "2"
                window.run_selected_with_dependencies()
                self.wait_for(lambda: window.analysis_runner is None)
                source.assert_called_once()
                window.show_node_parameters("Selected")
                window.parameter_edits["gain"].setText("4")
                window.run_selected_button.click()
                self.assertEqual([row["node_id"] for row in window.analysis_runner.rows], ["Selected"])
                self.assertFalse(window.run_with_dependencies_button.isEnabled())
                self.wait_for(lambda: window.analysis_runner is None)
                self.assertEqual(window.output_values["answer"], 12)
                source.assert_called_once()
                self.assertNotIn("必要前置分析", window.console.toPlainText())
                self.assertTrue(window.run_with_dependencies_button.isEnabled())
            finally:
                if window.analysis_runner is not None:
                    window.analysis_runner.wait(5000)
                    self.app.processEvents()
                window.close()

    def test_single_analysis_restores_saved_outputs_but_live_outputs_take_priority(self):
        source = MagicMock()
        plugins = [plugin("Source", source, outputs={"source_value": "value"}),
                   plugin("Selected", lambda p: response({"answer": p["source_value"] * 2}),
                          parameters={"source_value": "float"}, outputs={"answer": "answer"})]
        with TemporaryDirectory(dir=ROOT) as temporary, ExitStack() as stack:
            destination = Path(temporary)
            (destination / "Source").mkdir()
            (destination / "Source" / "result.csv").write_text(
                "category,name,number\n輸入量,source_value,999\n導出量,source_value,7\n", encoding="utf-8-sig")
            window = self.make_window(stack, destination, plugins)
            try:
                window.run_selected_analysis()
                self.wait_for(lambda: window.analysis_runner is None)
                self.assertEqual(window.output_values["answer"], 14)
                self.assertIn("已從儲存結果載入：source_value", window.console.toPlainText())
                window.parameter_values["source_value"] = "5"
                window.run_selected_analysis()
                self.wait_for(lambda: window.analysis_runner is None)
                self.assertEqual(window.output_values["answer"], 10)
                self.assertNotIn("已從儲存結果載入", window.console.toPlainText())
                source.assert_not_called()
            finally:
                if window.analysis_runner is not None:
                    window.analysis_runner.wait(5000)
                    self.app.processEvents()
                window.close()

    def test_incremental_buttons_update_selected_scope_then_other_affected_branch(self):
        source = MagicMock(side_effect=lambda p: response({"source_value": p["base"]}))
        selected = MagicMock(side_effect=lambda p: response({"answer": p["source_value"] * p["gain"]}))
        other = MagicMock(side_effect=lambda p: response({"other_answer": p["source_value"] + p["offset"]}))
        unrelated = MagicMock(side_effect=lambda p: response({"temperature_result": p["temperature"]}))
        plugins = [
            plugin("Source", source, parameters={"base": "float"}, outputs={"source_value": "value"}),
            plugin("Selected", selected, parameters={"source_value": "float", "gain": "float"},
                   outputs={"answer": "value"}),
            plugin("OtherBranch", other, parameters={"source_value": "float", "offset": "float"},
                   outputs={"other_answer": "value"}),
            plugin("Unrelated", unrelated, parameters={"temperature": "float"}, outputs={"temperature_result": "value"}),
        ]
        with TemporaryDirectory(dir=ROOT) as temporary, ExitStack() as stack:
            window = self.make_window(stack, Path(temporary), plugins)
            window.parameter_values = {"base": "3", "gain": "2", "offset": "5", "temperature": "1"}
            try:
                window.run_affected_button.click()
                self.assertFalse(window.run_affected_button.isEnabled())
                self.wait_for(lambda: window.analysis_runner is None)
                self.assertEqual([p.call_count for p in (source, selected, other, unrelated)], [1, 1, 1, 1])
                window.show_node_parameters("Selected")
                window.parameter_edits["gain"].setText("4")
                window.run_with_dependencies_button.click()
                self.wait_for(lambda: window.analysis_runner is None)
                self.assertEqual([p.call_count for p in (source, selected, other, unrelated)], [1, 2, 1, 1])
                self.assertEqual(window.output_values["answer"], 12)
                self.assertIn("沿用：Source", window.console.toPlainText())
                window.show_node_parameters("Source")
                window.parameter_edits["base"].setText("5")
                window.show_node_parameters("Selected")
                window.run_with_dependencies_button.click()
                self.wait_for(lambda: window.analysis_runner is None)
                self.assertEqual([p.call_count for p in (source, selected, other, unrelated)], [2, 3, 1, 1])
                window.run_affected_button.click()
                self.wait_for(lambda: window.analysis_runner is None)
                self.assertEqual([p.call_count for p in (source, selected, other, unrelated)], [2, 3, 2, 1])
                self.assertEqual(window.output_values["other_answer"], 10)
                self.assertIn("重算 1 項，沿用 3 項", window.status_label.text())
                window.run_affected_button.click()
                self.wait_for(lambda: window.analysis_runner is None)
                self.assertEqual([p.call_count for p in (source, selected, other, unrelated)], [2, 3, 2, 1])
                self.assertIn("重算 0 項，沿用 4 項", window.status_label.text())
                self.assertTrue(window.run_affected_button.isEnabled())
            finally:
                if window.analysis_runner is not None:
                    window.analysis_runner.wait(5000)
                    self.app.processEvents()
                window.close()

    def test_single_analysis_missing_or_invalid_upstream_never_falls_back_to_execution(self):
        source, selected = MagicMock(), MagicMock()
        plugins = [plugin("Source", source, outputs={"source_value": "value"}),
                   plugin("Selected", selected, parameters={"source_value": "float"})]
        with TemporaryDirectory(dir=ROOT) as temporary, ExitStack() as stack:
            window = self.make_window(stack, Path(temporary), plugins)
            warning = stack.enter_context(patch("main.QMessageBox.warning"))
            try:
                window.run_selected_analysis()
                self.assertIsNone(window.analysis_runner)
                self.assertIn("所選分析＋前置分析", warning.call_args.args[2])
                window.parameter_values["source_value"] = "bad value"
                window.run_selected_analysis()
                self.assertIsNone(window.analysis_runner)
                self.assertEqual(warning.call_count, 2)
                source.assert_not_called()
                selected.assert_not_called()
                self.assertTrue(window.run_button.isEnabled())
            finally:
                window.close()

    def test_manual_panel_values_stay_private_across_nodes_csv_reload_and_restart(self):
        plugins = [plugin("Source", MagicMock(), outputs={"ms": "mass"}),
                   plugin("Selected", MagicMock(), parameters={"ms": "float", "gain": "float"}),
                   plugin("Other", MagicMock(), parameters={"ms": "float", "gain": "float"})]
        plugins[1].hidden_parameters = {"ms"}
        with TemporaryDirectory(dir=ROOT) as temporary, ExitStack() as stack:
            folder = Path(temporary)
            window = self.make_window(stack, folder, plugins)
            try:
                window.parameter_values = {"ms": "260", "gain": "2"}
                window.output_values = {"ms": 260}
                window.show_node_parameters("Selected")
                self.assertNotIn("ms", window.parameter_edits)
                window.manual_parameters_checkbox.setChecked(True)
                self.assertEqual(set(window.parameter_edits), {"ms", "gain"})
                self.assertTrue(all(not edit.isReadOnly() for edit in window.parameter_edits.values()))
                window.parameter_edits["ms"].setText("100")
                window.parameter_edits["gain"].setText("3")
                saved = load_node_settings(folder / "last.nodes.json")
                self.assertTrue(saved["Selected"].manual)
                self.assertEqual(saved["Selected"].parameters, {"ms": "100", "gain": "3"})
                window.show_node_parameters("Other")
                self.assertFalse(window.manual_parameters_checkbox.isChecked())
                self.assertEqual(window.parameter_edits["gain"].text(), "2")
                window.manual_parameters_checkbox.setChecked(True)
                window.parameter_edits["ms"].setText("500")
                window.show_node_parameters("Selected")
                self.assertEqual(window.parameter_edits["ms"].text(), "100")
                window.manual_parameters_checkbox.setChecked(False)
                self.assertNotIn("ms", window.parameter_edits)
                self.assertEqual(window.parameter_edits["gain"].text(), "2")
                window.manual_parameters_checkbox.setChecked(True)
                self.assertEqual(window.parameter_edits["ms"].text(), "100")
                self.assertEqual(window.parameter_values, {"ms": "260", "gain": "2"})
                self.assertEqual(window.output_values, {"ms": 260})
                csv_path = folder / "inputs.csv"
                csv_path.write_text("name,number\ngain,9\nms,999\n", encoding="utf-8")
                self.assertTrue(window.load_csv(csv_path))
                self.assertEqual(window.parameter_edits["ms"].text(), "100")
                self.assertEqual(window.parameter_edits["gain"].text(), "3")
                self.assertEqual(window.parameter_values, {"gain": "9"})
                window.skip_analysis_checkbox.setChecked(True)
            finally:
                window.close()
            restored = self.make_window(stack, folder, plugins)
            try:
                restored.show_node_parameters("Selected")
                self.assertTrue(restored.manual_parameters_checkbox.isChecked())
                self.assertTrue(restored.skip_analysis_checkbox.isChecked())
                self.assertEqual(restored.parameter_edits["ms"].text(), "100")
                restored.show_node_parameters("Other")
                self.assertEqual(restored.parameter_edits["ms"].text(), "500")
                self.assertFalse(restored.skip_analysis_checkbox.isChecked())
            finally:
                restored.close()

    def test_skip_settings_are_saved_immediately_for_each_node_without_closing(self):
        plugins = [plugin("Source", MagicMock()), plugin("Selected", MagicMock())]
        with TemporaryDirectory(dir=ROOT) as temporary, ExitStack() as stack:
            folder = Path(temporary)
            window = self.make_window(stack, folder, plugins)
            path = folder / "last.nodes.json"
            try:
                initial = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(set(initial), {"Source", "Selected"})
                self.assertFalse(initial["Source"]["skip"])
                self.assertFalse(initial["Selected"]["skip"])
                window.show_node_parameters("Selected")
                window.skip_analysis_checkbox.setChecked(True)
                saved = load_node_settings(path)
                self.assertTrue(saved["Selected"].skip)
                self.assertFalse(saved["Source"].skip)
                window.show_node_parameters("Source")
                self.assertFalse(window.skip_analysis_checkbox.isChecked())
                window.show_node_parameters("Selected")
                self.assertTrue(window.skip_analysis_checkbox.isChecked())
                self.assertTrue(load_node_settings(path)["Selected"].skip)
                window.skip_analysis_checkbox.setChecked(False)
                self.assertFalse(load_node_settings(path)["Selected"].skip)
            finally:
                window.close()

    def test_all_four_buttons_honor_skip_before_validation_and_preserve_exports(self):
        for button in ("run_button", "run_selected_button", "run_with_dependencies_button", "run_affected_button"):
            with self.subTest(button=button), TemporaryDirectory(dir=ROOT) as temporary, ExitStack() as stack:
                source, selected = MagicMock(side_effect=lambda p: response({})), MagicMock()
                plugins = [plugin("Source", source),
                           plugin("Selected", selected, parameters={"missing": "float"})]
                plugins[1].required_analyses = ("Source",)
                folder = Path(temporary)
                result = folder / "Selected" / "result.csv"
                result.parent.mkdir()
                result.write_text("existing result", encoding="utf-8")
                window = self.make_window(stack, folder, plugins)
                try:
                    window.show_node_parameters("Selected")
                    window.manual_parameters_checkbox.setChecked(True)
                    window.skip_analysis_checkbox.setChecked(True)
                    getattr(window, button).click()
                    self.assertIsNotNone(window.analysis_runner)
                    runner = window.analysis_runner
                    if button in {"run_selected_button", "run_with_dependencies_button"}:
                        self.assertEqual([row["node_id"] for row in runner.rows], ["Selected"])
                    self.wait_for(lambda: window.analysis_runner is None)
                    self.assertIsNone(runner.error)
                    self.assertEqual(runner.skipped_count, 1)
                    selected.assert_not_called()
                    self.assertEqual(source.call_count, int(button in {"run_button", "run_affected_button"}))
                    self.assertEqual(result.read_text(encoding="utf-8"), "existing result")
                    self.assertIn("跳過：Selected", window.console.toPlainText())
                    self.assertIn("跳過 1 項", window.status_label.text())
                finally:
                    if window.analysis_runner is not None:
                        window.analysis_runner.wait(5000)
                        self.app.processEvents()
                    window.close()

    def test_all_four_buttons_apply_manual_inputs_without_overwriting_shared_mass(self):
        for button in ("run_button", "run_selected_button", "run_with_dependencies_button", "run_affected_button"):
            with self.subTest(button=button), TemporaryDirectory(dir=ROOT) as temporary, ExitStack() as stack:
                source = MagicMock(side_effect=lambda p: response({"ms": 300}))
                selected = MagicMock(side_effect=lambda p: response({"answer": p["ms"] * p["gain"]}))
                plugins = [plugin("Source", source, outputs={"ms": "mass"}),
                           plugin("Selected", selected, parameters={"ms": "float", "gain": "float"},
                                  outputs={"answer": "answer"})]
                plugins[1].required_analyses = ("Source",)
                window = self.make_window(stack, Path(temporary), plugins)
                try:
                    window.parameter_values = {"ms": "260", "gain": "2"}
                    window.output_values = {"ms": 260}
                    window.show_node_parameters("Selected")
                    window.manual_parameters_checkbox.setChecked(True)
                    window.parameter_edits["ms"].setText("100")
                    window.parameter_edits["gain"].setText("4")
                    getattr(window, button).click()
                    self.assertIsNotNone(window.analysis_runner)
                    self.assertFalse(window.parameter_options.isEnabled())
                    if button in {"run_selected_button", "run_with_dependencies_button"}:
                        self.assertEqual([row["node_id"] for row in window.analysis_runner.rows], ["Selected"])
                    self.wait_for(lambda: window.analysis_runner is None)
                    selected.assert_called_once_with({"ms": 100.0, "gain": 4.0})
                    self.assertEqual(window.parameter_values["gain"], "2")
                    expected_mass = 300 if button in {"run_button", "run_affected_button"} else 260
                    self.assertEqual(float(window.parameter_values["ms"]), expected_mass)
                    self.assertEqual(window.output_values["ms"], expected_mass)
                    self.assertEqual(window.output_values["answer"], 400)
                    self.assertEqual(window.parameter_edits["ms"].text(), "100")
                    self.assertTrue(window.parameter_options.isEnabled())
                finally:
                    if window.analysis_runner is not None:
                        window.analysis_runner.wait(5000)
                        self.app.processEvents()
                    window.close()

    def test_manual_selected_runs_without_any_upstream_results_and_invalid_manual_input_is_rejected(self):
        source = MagicMock()
        selected = MagicMock(side_effect=lambda p: response({"answer": p["ms"]}))
        plugins = [plugin("Source", source, parameters={"missing_source_input": "float"}, outputs={"ms": "mass"}),
                   plugin("Selected", selected, parameters={"ms": "float"}, outputs={"answer": "answer"})]
        with TemporaryDirectory(dir=ROOT) as temporary, ExitStack() as stack:
            warning = stack.enter_context(patch("main.QMessageBox.warning"))
            window = self.make_window(stack, Path(temporary), plugins)
            try:
                window.show_node_parameters("Selected")
                window.manual_parameters_checkbox.setChecked(True)
                for value in ("", "invalid"):
                    window.parameter_edits["ms"].setText(value)
                    for button in (window.run_selected_button, window.run_with_dependencies_button):
                        button.click()
                        self.assertIsNone(window.analysis_runner)
                self.assertEqual(warning.call_count, 4)
                selected.assert_not_called()
                window.parameter_edits["ms"].setText("100")
                for button in (window.run_selected_button, window.run_with_dependencies_button):
                    button.click()
                    self.wait_for(lambda: window.analysis_runner is None)
                self.assertEqual(selected.call_count, 2)
                source.assert_not_called()
                self.assertNotIn("ms", window.parameter_values)
                self.assertNotIn("ms", window.output_values)
            finally:
                window.close()

    def test_skipped_upstream_uses_saved_output_and_never_runs_its_own_dependencies(self):
        source = MagicMock()
        selected = MagicMock(side_effect=lambda p: response({"answer": p["ms"] * 2}))
        plugins = [plugin("Source", source, parameters={"missing": "float"}, outputs={"ms": "mass"}),
                   plugin("Selected", selected, parameters={"ms": "float"}, outputs={"answer": "answer"})]
        with TemporaryDirectory(dir=ROOT) as temporary, ExitStack() as stack:
            folder = Path(temporary)
            (folder / "Source").mkdir()
            result = folder / "Source" / "result.csv"
            content = "category,name,number\n導出量,ms,260\n"
            result.write_text(content, encoding="utf-8")
            window = self.make_window(stack, folder, plugins)
            try:
                window.node_settings["Source"] = NodeSettings(skip=True)
                window.run_selected_with_dependencies()
                self.wait_for(lambda: window.analysis_runner is None)
                selected.assert_called_once_with({"ms": 260.0})
                source.assert_not_called()
                self.assertEqual(window.output_values["answer"], 520)
                self.assertEqual(result.read_text(encoding="utf-8"), content)
                self.assertIn("跳過：Source", window.console.toPlainText())
            finally:
                if window.analysis_runner is not None:
                    window.analysis_runner.wait(5000)
                    self.app.processEvents()
                window.close()

    def test_failure_reports_current_stage_and_restores_controls_and_stdout(self):
        original_stdout = sys.stdout
        third = MagicMock()

        def fail(parameters):
            raise ValueError("expected test failure")

        plugins = [plugin("First", lambda parameters: response({})),
                   plugin("Failed", fail), plugin("MustNotRun", third)]
        with TemporaryDirectory(dir=ROOT) as temporary, ExitStack() as stack:
            destination = Path(temporary).resolve()
            self.assertTrue(destination.is_relative_to(ROOT.resolve()))
            message = stack.enter_context(patch("main.QMessageBox.critical"))
            window = self.make_window(stack, destination, plugins)
            try:
                window.run_flow()
                self.wait_for(lambda: window.analysis_runner is None)
                self.assertIn("[1/3] 完成：First", window.console.toPlainText())
                self.assertIn("分析中止：Failed：expected test failure", window.console.toPlainText())
                self.assertNotIn("全部完成", window.console.toPlainText())
                self.assertFalse(window.progress_timer.isActive())
                self.assertTrue(window.run_button.isEnabled())
                self.assertTrue(window.run_selected_button.isEnabled())
                self.assertTrue(window.run_with_dependencies_button.isEnabled())
                self.assertTrue(window.run_affected_button.isEnabled())
                self.assertTrue(window.csv_button.isEnabled())
                self.assertTrue(window.parameter_scroll.isEnabled())
                self.assertIs(sys.stdout, original_stdout)
                third.assert_not_called()
                message.assert_called_once()
            finally:
                if window.analysis_runner is not None:
                    window.analysis_runner.wait(5000)
                    self.app.processEvents()
                window.close()

    def test_log_stream_preserves_partial_prints_and_flush(self):
        lines = []
        stream = LogStream(lines.append)
        self.assertEqual(stream.write("partial "), 8)
        self.assertEqual(lines, [])
        stream.write("line\nnext")
        self.assertEqual(lines, ["partial line"])
        stream.flush()
        self.assertEqual(lines, ["partial line", "next"])


if __name__ == "__main__":
    unittest.main()
