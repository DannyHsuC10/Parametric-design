"""Run analyses and export figures while the Qt interface stays responsive."""

from contextlib import redirect_stderr, redirect_stdout
import io
from time import perf_counter

import matplotlib
matplotlib.use("Agg")
from PySide6.QtCore import QThread, Signal

from analysis_data import parse_analysis_parameters
from analysis_result import normalize_result, save_analysis_result


class LogStream(io.TextIOBase):
    def __init__(self, emit):
        super().__init__()
        self.emit = emit
        self.pending = ""

    def write(self, text):
        self.pending += text
        while "\n" in self.pending:
            line, self.pending = self.pending.split("\n", 1)
            if line.strip():
                self.emit(line.rstrip())
        return len(text)

    def flush(self):
        if self.pending.strip():
            self.emit(self.pending.rstrip())
        self.pending = ""


class AnalysisRunner(QThread):
    log = Signal(str)
    stageStarted = Signal(int, int, str)
    stageSaving = Signal()
    stageCompleted = Signal(int, int, str, object, float)

    def __init__(self, plugins, rows, values, results_dir, selected_node_id=None, parent=None):
        super().__init__(parent)
        self.plugins = plugins
        self.rows = [dict(row) for row in rows]
        self.values = dict(values)
        self.results_dir = results_dir
        self.selected_node_id = selected_node_id
        self.error = None
        self.elapsed = 0.0
        self.completed_count = 0

    def run(self):
        started = perf_counter()
        output, errors = LogStream(self.log.emit), LogStream(self.log.emit)
        current_title = ""
        with redirect_stdout(output), redirect_stderr(errors):
            try:
                total = len(self.rows)
                for position, row in enumerate(self.rows, start=1):
                    current_title = row["title"]
                    label = ""
                    if self.selected_node_id:
                        label = "所選分析｜" if row["node_id"] == self.selected_node_id else "必要前置分析｜"
                    self.stageStarted.emit(position, total, current_title)
                    print(f"[{position}/{total}] 開始：{label}{current_title}", flush=True)
                    stage_started = perf_counter()
                    plugin = self.plugins[row["analysis_id"]]
                    parameters = parse_analysis_parameters(self.values, plugin.parameters)
                    result = normalize_result(plugin.run(parameters))
                    try:
                        self.stageSaving.emit()
                        print(f"[{position}/{total}] 計算完成，正在儲存圖表與結果：{current_title}", flush=True)
                        save_analysis_result(self.results_dir, row["node_id"], parameters, result)
                        for name, value in result.outputs.items():
                            self.values[name] = str(value)
                        elapsed = perf_counter() - stage_started
                        self.completed_count = position
                        self.stageCompleted.emit(position, total, current_title, dict(result.outputs), elapsed)
                        print(f"[{position}/{total}] 完成：{current_title}（耗時 {elapsed:.2f} 秒，結果已儲存）", flush=True)
                    finally:
                        result.close()
                print(f"全部完成：{total}/{total} 項分析，總耗時 {perf_counter() - started:.2f} 秒。", flush=True)
            except Exception as error:
                self.error = f"{current_title}：{error}"
                print(f"分析中止：{self.error}", flush=True)
            finally:
                output.flush()
                errors.flush()
                self.elapsed = perf_counter() - started
