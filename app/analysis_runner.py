"""Run analyses and export figures while the Qt interface stays responsive."""

from contextlib import redirect_stderr, redirect_stdout
import io
from time import perf_counter

import matplotlib
matplotlib.use("Agg")
from PySide6.QtCore import QThread, Signal

from .analysis_data import parse_analysis_parameters
from .analysis_cache import begin_analysis, input_file_state, remember_analysis, reusable_outputs, saved_outputs
from .analysis_result import normalize_result, save_analysis_result
from .analysis_settings import NodeSettings


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
    stageReused = Signal(int, int, str, object)
    stageSkipped = Signal(int, int, str, object)

    def __init__(self, plugins, rows, values, results_dir, selected_node_id=None, parent=None, *,
                 incremental=False, node_settings=None):
        super().__init__(parent)
        self.plugins = plugins
        self.rows = [dict(row) for row in rows]
        self.values = dict(values)
        self.results_dir = results_dir
        self.selected_node_id = selected_node_id
        self.incremental = incremental
        self.node_settings = {node: NodeSettings(skip=options.skip, manual=options.manual,
                                               parameters=dict(options.parameters), nonessential=options.nonessential)
                              for node, options in (node_settings or {}).items()}
        self.error = None
        self.elapsed = 0.0
        self.completed_count = 0
        self.reused_count = 0
        self.skipped_count = 0

    def run(self):
        started = perf_counter()
        output, errors = LogStream(self.log.emit), LogStream(self.log.emit)
        current_title = ""
        with redirect_stdout(output), redirect_stderr(errors):
            try:
                total = len(self.rows)
                skipped_outputs = {name for row in self.rows
                                   if self.node_settings.get(row["node_id"], NodeSettings()).skip
                                   for name in self.plugins[row["analysis_id"]].outputs}
                for position, row in enumerate(self.rows, start=1):
                    current_title = row["title"]
                    plugin = self.plugins[row["analysis_id"]]
                    options = self.node_settings.get(row["node_id"], NodeSettings())
                    if options.skip:
                        restored = {name: value for name, value in
                                    saved_outputs(self.results_dir, row["node_id"], plugin.outputs).items()
                                    if not str(self.values.get(name, "")).strip()}
                        self.values.update(restored)
                        self.skipped_count += 1
                        self.stageSkipped.emit(position, total, current_title, restored)
                        print(f"[{position}/{total}] 跳過：{current_title}（已勾選跳過此分析，保留既有結果）", flush=True)
                        continue
                    values = options.parameters if options.manual else self.values
                    missing_skipped = {name for name in plugin.parameters if name in skipped_outputs
                                       and not str(values.get(name, "")).strip()}
                    if missing_skipped and not options.manual:
                        raise ValueError("已跳過的前置分析沒有可沿用的結果：" + ", ".join(sorted(missing_skipped))
                                         + "。請取消跳過該前置分析，或在本分析勾選全部參數手動設定。")
                    parameters = parse_analysis_parameters(values, plugin.parameters)
                    files = input_file_state(plugin)
                    if self.incremental and row["node_id"] != self.selected_node_id:
                        cached = reusable_outputs(self.results_dir, row, plugin, parameters, files)
                        if cached is not None:
                            self.values.update(cached)
                            self.reused_count += 1
                            self.stageReused.emit(position, total, current_title, cached)
                            print(f"[{position}/{total}] 沿用：{current_title}（輸入與來源資料未變，略過重算）", flush=True)
                            continue
                    label = ""
                    if self.selected_node_id:
                        label = "所選分析｜" if row["node_id"] == self.selected_node_id else "必要前置分析｜"
                    if options.manual:
                        label += "全部參數手動設定｜"
                    self.stageStarted.emit(position, total, current_title)
                    print(f"[{position}/{total}] 開始：{label}{current_title}", flush=True)
                    stage_started = perf_counter()
                    begin_analysis(self.results_dir, row["node_id"])
                    result = normalize_result(plugin.run(parameters))
                    try:
                        self.stageSaving.emit()
                        print(f"[{position}/{total}] 計算完成，正在儲存圖表與結果：{current_title}", flush=True)
                        save_analysis_result(self.results_dir, row["node_id"], parameters, result)
                        remember_analysis(self.results_dir, row, parameters, result.outputs, files)
                        for name, value in result.outputs.items():
                            self.values[name] = str(value)
                        elapsed = perf_counter() - stage_started
                        self.completed_count += 1
                        self.stageCompleted.emit(position, total, current_title, dict(result.outputs), elapsed)
                        print(f"[{position}/{total}] 完成：{current_title}（耗時 {elapsed:.2f} 秒，結果已儲存）", flush=True)
                    finally:
                        result.close()
                if self.incremental:
                    print(f"全部完成：重算 {self.completed_count} 項，沿用 {self.reused_count} 項，"
                          f"跳過 {self.skipped_count} 項，總耗時 {perf_counter() - started:.2f} 秒。", flush=True)
                else:
                    print(f"全部完成：{self.completed_count}/{total} 項分析，跳過 {self.skipped_count} 項，"
                          f"總耗時 {perf_counter() - started:.2f} 秒。", flush=True)
            except Exception as error:
                self.error = f"{current_title}：{error}"
                print(f"分析中止：{self.error}", flush=True)
            finally:
                output.flush()
                errors.flush()
                self.elapsed = perf_counter() - started
