"""Progress is visible before the next analysis finishes, with a live Qt event loop."""

from contextlib import ExitStack
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

from analysis_runner import AnalysisRunner, LogStream
from main import MainWindow
from plugin_loader import AnalysisPlugin

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
