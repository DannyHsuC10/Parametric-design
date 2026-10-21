import csv
import json
import re
import sys
from pathlib import Path
from time import perf_counter, time

from PySide6.QtCore import QTimer, QSize, Qt, Signal, Slot, QUrlQuery
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from analysis_data import canonical_parameter_name, load_analysis_parameters
from analysis_result import AnalysisResult, load_plot_choices, save_analysis_result
from analysis_runner import AnalysisRunner
from document_theme import document_colors
from markdown_renderer import render_markdown, render_markdown_file
from markdown_view import MarkdownView
from plugin_loader import scan_analysis

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"
DEFAULT_CSV = DATA_DIR / "analysis_parameters.csv"
FLOW_CSV = DATA_DIR / "analysis_flow.csv"
LAST_SET_CSV = DATA_DIR / "analysis_parameters_last_set.csv"
RESULTS_DIR = DATA_DIR / "results"


class FlowDiagramPage(QWebEnginePage):
    flowNodeRequested = Signal(str, bool)

    def acceptNavigationRequest(self, url, navigation_type, is_main_frame):
        if url.scheme() == "flow-node":
            node_id = url.path().strip("/")
            is_double_click = url.host() == "double"
            received_at = perf_counter()
            try:
                clicked_at_ms = float(QUrlQuery(url).queryItemValue("clicked_at"))
                transport_ms = max(0.0, time()*1000-clicked_at_ms)
            except ValueError:
                transport_ms = None

            def dispatch():
                self.last_request_delay_ms = (transport_ms + (perf_counter()-received_at)*1000
                                              if transport_ms is not None else None)
                self.flowNodeRequested.emit(node_id, is_double_click)

            QTimer.singleShot(0, dispatch)
            return False
        return super().acceptNavigationRequest(url, navigation_type, is_main_frame)


class ResultDialog(QDialog):
    firstFrameReady = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._first_paint_seen = False

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._first_paint_seen:
            self._first_paint_seen = True
            QTimer.singleShot(0, self, self.firstFrameReady.emit)


class ScalableImageLabel(QLabel):
    def __init__(self):
        super().__init__()
        self.original_pixmap = QPixmap()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(260)

    def set_image(self, path):
        self.original_pixmap = QPixmap(str(path))
        self.update_pixmap()

    def update_pixmap(self):
        if not self.original_pixmap.isNull():
            ratio = self.devicePixelRatioF()
            physical_size = QSize(
                round(self.width() * ratio),
                round(self.height() * ratio),
            )
            scaled = self.original_pixmap.scaled(
                physical_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            scaled.setDevicePixelRatio(ratio)
            self.setPixmap(scaled)
        else:
            self.setText("找不到結果圖表")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_pixmap()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vehicle Dynamics Toolbox")
        self.resize(1200, 800)

        self.plugins = scan_analysis()
        self.plugins_by_id = {plugin.plugin_id: plugin for plugin in self.plugins}
        self.flow = self.load_flow()
        self.csv_path = DEFAULT_CSV
        self.parameter_values = {}
        self.output_names = {name for plugin in self.plugins for name in plugin.outputs}
        self.output_values = {}
        self.parameter_edits = {}
        self.active_node_id = None
        self.plot = None
        self.analysis_runner = None
        self.progress_timer = QTimer(self)
        self.progress_timer.setInterval(250)
        self.progress_timer.timeout.connect(self._refresh_analysis_status)

        self.csv_button = QPushButton("選擇參數 CSV")
        self.csv_label = QLabel()
        self.csv_label.setWordWrap(True)
        self.database_button = QPushButton("檢視目前變量")
        self.run_button = QPushButton("Run 全流程")
        self.run_selected_button = QPushButton("單獨執行所選分析")
        self.run_selected_button.setEnabled(False)
        self.status_label = QLabel("選擇 CSV 後按 Run，依流程順序執行分析。")

        self.flow_view = QWebEngineView()
        self.flow_view.setMinimumHeight(120)
        self.flow_page = FlowDiagramPage(self.flow_view)
        self.flow_page.setBackgroundColor(QColor(document_colors()["background"]))
        self.flow_view.setPage(self.flow_page)
        self.flow_view.settings().setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptEnabled, True
        )
        self.flow_page.flowNodeRequested.connect(self.handle_flow_node_request)
        self.build_flow_buttons()

        self.parameter_form = QFormLayout()
        self.parameter_panel = QWidget()
        self.parameter_panel.setLayout(self.parameter_form)
        self.parameter_scroll = QScrollArea()
        self.parameter_scroll.setWidgetResizable(True)
        self.parameter_scroll.setWidget(self.parameter_panel)
        self.parameter_scroll.setMinimumHeight(120)
        self.parameter_title = QLabel("輸入參數（單擊流程節點以設定）")
        self.console = QTextEdit()
        self.console.setReadOnly(True)

        controls = QHBoxLayout()
        controls.addWidget(self.csv_button)
        controls.addWidget(self.database_button)
        controls.addWidget(self.csv_label, 1)
        controls.addWidget(self.run_button)
        controls.addWidget(self.run_selected_button)

        parameter_section = QWidget()
        parameter_layout = QVBoxLayout(parameter_section)
        parameter_layout.setContentsMargins(0, 0, 0, 0)
        parameter_layout.addWidget(self.parameter_title)
        parameter_layout.addWidget(self.parameter_scroll)

        console_section = QWidget()
        console_layout = QVBoxLayout(console_section)
        console_layout.setContentsMargins(0, 0, 0, 0)
        console_layout.addWidget(QLabel("Print out／執行輸出"))
        console_layout.addWidget(self.console)

        self.work_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.work_splitter.setChildrenCollapsible(False)
        self.work_splitter.setHandleWidth(8)
        self.work_splitter.addWidget(parameter_section)
        self.work_splitter.addWidget(console_section)
        self.work_splitter.setStretchFactor(0, 2)
        self.work_splitter.setStretchFactor(1, 3)
        self.work_splitter.setSizes([480, 720])
        self.work_splitter.handle(1).setToolTip("左右拖曳，調整參數與 Print out 區域寬度")

        flow_section = QWidget()
        flow_layout = QVBoxLayout(flow_section)
        flow_layout.setContentsMargins(0, 0, 0, 0)
        flow_layout.addWidget(self.flow_view, 1)
        flow_layout.addWidget(self.status_label)

        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setHandleWidth(8)
        self.main_splitter.addWidget(flow_section)
        self.main_splitter.addWidget(self.work_splitter)
        self.main_splitter.setStretchFactor(0, 2)
        self.main_splitter.setStretchFactor(1, 3)
        self.main_splitter.setSizes([300, 440])
        self.main_splitter.handle(1).setToolTip("上下拖曳，調整流程圖與下方工作區高度")

        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addWidget(QLabel("單擊節點設定參數；雙擊查看結果；也可單獨執行所選分析（必要時會先跑前置分析）"))
        layout.addWidget(self.main_splitter, 1)

        self.csv_button.clicked.connect(self.select_csv)
        self.database_button.clicked.connect(self.show_database)
        self.run_button.clicked.connect(self.run_flow)
        self.run_selected_button.clicked.connect(self.run_selected_analysis)

        self.load_csv(DEFAULT_CSV)
        QTimer.singleShot(0, self.select_csv)

    def load_flow(self, path=FLOW_CSV):
        try:
            with path.open("r", newline="", encoding="utf-8-sig") as flow_file:
                reader = csv.DictReader(flow_file)
                required = {"order", "node_id", "title", "analysis_id"}
                if reader.fieldnames is None or not required.issubset(reader.fieldnames):
                    raise ValueError("流程設定 CSV 需要 order,node_id,title,analysis_id 欄位")
                rows = list(reader)
        except (OSError, ValueError) as error:
            QMessageBox.critical(self, "流程設定載入失敗", str(error))
            return []

        try:
            rows.sort(key=lambda row: int(row["order"]))
            node_ids = set()
            for row in rows:
                row.setdefault("flow_row", "main")
                row.setdefault("branch_from", "")
                row["flow_group"] = (row.get("flow_group") or "").strip()
                row["merge_from"] = (row.get("merge_from") or "").strip()
                node_id = row["node_id"].strip()
                analysis_id = row["analysis_id"].strip()
                flow_row = row["flow_row"].strip() or "main"
                branch_from = row["branch_from"].strip()
                merge_from = row["merge_from"]
                merge_sources = [source.strip() for source in merge_from.split("|") if source.strip()]
                if not re.fullmatch(r"[A-Za-z0-9_-]+", node_id):
                    raise ValueError(f"無效的節點名稱：{node_id}")
                if flow_row not in {"main", "branch", "secondary", "tertiary", "merge"}:
                    raise ValueError(f"無效的流程列名稱：{flow_row}")
                if branch_from and branch_from not in node_ids:
                    raise ValueError(f"分支節點 {node_id} 的來源不存在或順序錯誤：{branch_from}")
                if flow_row == "branch" and not branch_from:
                    raise ValueError(f"分支節點 {node_id} 必須設定 branch_from")
                for source in merge_sources:
                    if source not in node_ids:
                        raise ValueError(f"匯合節點 {node_id} 的來源不存在或順序錯誤：{source}")
                if flow_row == "merge" and (not branch_from or not merge_sources):
                    raise ValueError(f"匯合節點 {node_id} 必須設定 branch_from 與 merge_from")
                if node_id in node_ids:
                    raise ValueError(f"節點名稱重複：{node_id}")
                if analysis_id not in self.plugins_by_id:
                    raise ValueError(f"找不到分析插件：{analysis_id}")
                if not row["title"].strip():
                    raise ValueError(f"節點 {node_id} 缺少 title")
                node_ids.add(node_id)
                row["node_id"] = node_id
                row["title"] = row["title"].strip()
                row["analysis_id"] = analysis_id
                row["flow_row"] = flow_row
                row["branch_from"] = branch_from
                row["merge_from"] = "|".join(merge_sources)
            return rows
        except (KeyError, ValueError) as error:
            QMessageBox.critical(self, "流程設定錯誤", str(error))
            return []

    def build_flow_buttons(self, flow=None, view=None):
        flow = self.flow if flow is None else flow
        view = self.flow_view if view is None else view
        graph_ids = {
            row["node_id"]: f"flow_node_{index}"
            for index, row in enumerate(flow)
        }
        lines = ["graph TD"]
        main_rows = [row for row in flow if row["flow_row"] == "main"]
        branch_rows = [row for row in flow if row["flow_row"] == "branch"]
        secondary_rows = [row for row in flow if row["flow_row"] == "secondary"]
        tertiary_rows = [row for row in flow if row["flow_row"] == "tertiary"]
        merge_rows = [row for row in flow if row["flow_row"] == "merge"]

        def connect_chain(rows):
            for first, second in zip(rows, rows[1:]):
                lines.append(f"    {graph_ids[first['node_id']]} --> {graph_ids[second['node_id']]}")

        connect_chain(main_rows)
        for row in branch_rows:
            lines.append(f"    {graph_ids[row['branch_from']]} --> {graph_ids[row['node_id']]}")
        connect_chain(secondary_rows)
        connect_chain(tertiary_rows)
        for row in merge_rows:
            merge_id = graph_ids[row["node_id"]]
            sources = [row["branch_from"]] + (row.get("merge_from") or "").split("|")
            for source in dict.fromkeys(source.strip() for source in sources if source.strip()):
                lines.append(f"    {graph_ids[source]} --> {merge_id}")

        groups = {}
        for row in flow:
            groups.setdefault(row.get("flow_group", ""), []).append(row)
        for index, (group, rows) in enumerate(groups.items()):
            if group:
                title = group.replace('"', "&quot;")
                lines.append(f'    subgraph flow_group_{index}["{title}"]')
            for row in rows:
                graph_id = graph_ids[row["node_id"]]
                title = row["title"].replace('"', "&quot;")
                lines.append(f'    {graph_id}["{title}"]')
            if group:
                lines.append("    end")

        diagram_markdown = "```mermaid\n" + "\n".join(lines) + "\n```"
        rendered_html = render_markdown(diagram_markdown)
        click_map = {
            row["title"]: row["node_id"]
            for row in flow
        }
        click_map_json = json.dumps(click_map, ensure_ascii=True).replace("</", "<\\/")
        click_script = f"""<script>
(() => {{
  const titleToId = {click_map_json};
  let clickTimer = null;
  function findNode(event) {{
    const group = event.target.closest('g.node');
    if (!group) return null;
    const title = (group.textContent || '').replace(/\\s+/g, ' ').trim();
    return titleToId[title] || null;
  }}
  function request(nodeId, kind, clickedAt) {{
    window.location.href = 'flow-node://' + kind + '/' + encodeURIComponent(nodeId)
      + '?clicked_at=' + clickedAt;
  }}
  document.addEventListener('click', event => {{
    const nodeId = findNode(event);
    if (!nodeId) return;
    clearTimeout(clickTimer);
    const clickedAt = performance.timeOrigin + event.timeStamp;
    clickTimer = setTimeout(() => request(nodeId, 'single', clickedAt), 260);
  }});
  document.addEventListener('dblclick', event => {{
    const nodeId = findNode(event);
    if (!nodeId) return;
    clearTimeout(clickTimer);
    request(nodeId, 'double', performance.timeOrigin + event.timeStamp);
  }});
}})();
</script>"""
        rendered_html = rendered_html.replace("</body>", click_script + "</body>")
        view.setHtml(rendered_html)

    def handle_flow_node_request(self, node_id, is_double_click):
        if self.analysis_runner is not None:
            return
        if is_double_click:
            self._result_request_delay_ms = getattr(self.flow_page, "last_request_delay_ms", None)
            self.show_result(node_id)
        else:
            self.show_node_parameters(node_id)

    def load_csv(self, path):
        try:
            parameters = load_analysis_parameters(path)
        except (OSError, ValueError) as error:
            QMessageBox.critical(self, "CSV 載入失敗", str(error))
            return False

        self.csv_path = Path(path)
        defaults = {
            name: str(value)
            for plugin in self.plugins
            for name, value in plugin.parameter_defaults.items()
        }
        self.parameter_values = defaults | parameters
        self.output_values = {
            name: value for name, value in parameters.items() if name in self.output_names
        }
        self.csv_label.setText(str(self.csv_path))
        if self.active_node_id:
            self.show_node_parameters(self.active_node_id)
        else:
            self.build_parameter_fields(None)
        return True

    def build_parameter_fields(self, plugin):
        while self.parameter_form.rowCount():
            self.parameter_form.removeRow(0)
        self.parameter_edits.clear()
        if plugin is None:
            return
        for name in plugin.parameters:
            if name in plugin.hidden_parameters:
                continue
            edit = QLineEdit(self.parameter_values.get(name, ""))
            edit.textChanged.connect(lambda value, key=name: self.update_parameter(key, value))
            self.parameter_form.addRow(name, edit)
            self.parameter_edits[name] = edit

    def show_node_parameters(self, node_id):
        row = next((item for item in self.flow if item["node_id"] == node_id), None)
        if row is None:
            return
        self.active_node_id = node_id
        self.run_selected_button.setEnabled(True)
        plugin = self.plugins_by_id[row["analysis_id"]]
        self.parameter_title.setText(f"{row['title']} 輸入參數")
        self.build_parameter_fields(plugin)

    def update_parameter(self, name, value):
        name = canonical_parameter_name(name)
        self.parameter_values[name] = value
        for output_name in self.output_names:
            self.output_values.pop(output_name, None)
            self.parameter_values.pop(output_name, None)

    def select_csv(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "選擇分析參數 CSV", str(self.csv_path.parent), "CSV 檔案 (*.csv)"
        )
        if filename:
            self.load_csv(filename)

    def show_database(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("目前資料變量")
        dialog.resize(520, 380)
        layout = QVBoxLayout(dialog)
        table = QTableWidget(0, 3)
        table.setHorizontalHeaderLabels(["類別", "變量名稱", "數值"])
        table.horizontalHeader().setStretchLastSection(True)

        for name, value in self.parameter_values.items():
            if name in self.output_names:
                continue
            self.add_variable_row(table, "輸入量", name, value)
        for name, value in self.output_values.items():
            self.add_variable_row(table, "導出量", name, value)

        layout.addWidget(table)
        dialog.exec()

    @staticmethod
    def add_variable_row(table, category, name, value):
        row = table.rowCount()
        table.insertRow(row)
        for column, cell in enumerate((category, name, value)):
            table.setItem(row, column, QTableWidgetItem(str(cell)))

    def run_flow(self):
        if self.analysis_runner is not None:
            return
        if not self.flow:
            QMessageBox.warning(self, "沒有分析流程", "請檢查 data/analysis_flow.csv")
            return

        try:
            available_parameters = set(self.parameter_values)
            for row in self.flow:
                plugin = self.plugins_by_id[row["analysis_id"]]
                missing = set(plugin.parameters) - available_parameters
                if missing:
                    raise ValueError(
                        f"{row['title']} 缺少參數：{', '.join(sorted(missing))}"
                    )
                available_parameters.update(plugin.outputs)
        except ValueError as error:
            self.status_label.setText(f"參數尚未完成：{error}")
            QMessageBox.warning(self, "參數錯誤", str(error))
            return

        self._start_analysis(self.flow)

    def _required_analysis_rows(self, selected_node_id):
        selected_row = next(
            (row for row in self.flow if row["node_id"] == selected_node_id),
            None,
        )
        if selected_row is None:
            raise ValueError("找不到所選分析節點")

        producer_by_output = {}
        for row in self.flow:
            plugin = self.plugins_by_id[row["analysis_id"]]
            for output_name in plugin.outputs:
                producer_by_output[output_name] = row

        required_node_ids = set()
        visiting = set()

        def include_dependencies(row):
            node_id = row["node_id"]
            if node_id in required_node_ids:
                return
            if node_id in visiting:
                raise ValueError(f"分析依賴形成循環：{node_id}")
            visiting.add(node_id)
            plugin = self.plugins_by_id[row["analysis_id"]]
            for dependency in getattr(plugin, "required_analyses", ()):
                dependency_row = next((item for item in self.flow if item["node_id"] == dependency), None)
                if dependency_row is None:
                    raise ValueError(f"{row['title']} 找不到前置分析：{dependency}")
                include_dependencies(dependency_row)
            for parameter_name in plugin.parameters:
                current_value = self.parameter_values.get(parameter_name)
                producer_row = producer_by_output.get(parameter_name)
                if current_value is not None and str(current_value).strip():
                    continue
                if producer_row is None:
                    raise ValueError(f"{row['title']} 缺少輸入參數：{parameter_name}")
                include_dependencies(producer_row)
            visiting.remove(node_id)
            required_node_ids.add(node_id)

        include_dependencies(selected_row)
        return [row for row in self.flow if row["node_id"] in required_node_ids]

    def run_selected_analysis(self):
        if self.analysis_runner is not None:
            return
        if not self.active_node_id:
            QMessageBox.information(self, "尚未選擇分析", "請先單擊流程圖中的分析節點。")
            return

        try:
            selected_rows = self._required_analysis_rows(self.active_node_id)
        except ValueError as error:
            self.status_label.setText(f"無法執行所選分析：{error}")
            QMessageBox.warning(self, "分析參數錯誤", str(error))
            return

        self._start_analysis(selected_rows, self.active_node_id)

    def _start_analysis(self, rows, selected_node_id=None):
        self.console.clear()
        self.run_button.setEnabled(False)
        self.run_selected_button.setEnabled(False)
        self.csv_button.setEnabled(False)
        self.parameter_scroll.setEnabled(False)
        self._run_started_at = perf_counter()
        self._stage_started_at = self._run_started_at
        self._stage_position = 0
        self._stage_total = len(rows)
        self._stage_title = "準備分析"
        self._stage_phase = "準備中"
        runner = AnalysisRunner(self.plugins_by_id, rows, self.parameter_values, RESULTS_DIR,
                                selected_node_id, parent=self)
        self.analysis_runner = runner
        runner.log.connect(self._append_analysis_log)
        runner.stageStarted.connect(self._analysis_stage_started)
        runner.stageSaving.connect(self._analysis_stage_saving)
        runner.stageCompleted.connect(self._analysis_stage_completed)
        runner.finished.connect(self._analysis_finished)
        self._refresh_analysis_status()
        self.progress_timer.start()
        runner.start()

    @Slot(str)
    def _append_analysis_log(self, text):
        self.console.append(text)
        self.console.ensureCursorVisible()

    @Slot(int, int, str)
    def _analysis_stage_started(self, position, total, title):
        self._stage_position, self._stage_total, self._stage_title = position, total, title
        self._stage_started_at = perf_counter()
        self._stage_phase = "分析中"
        self._refresh_analysis_status()

    @Slot()
    def _analysis_stage_saving(self):
        self._stage_phase = "儲存中"
        self._refresh_analysis_status()

    @Slot(int, int, str, object, float)
    def _analysis_stage_completed(self, position, total, title, outputs, elapsed):
        for name, value in outputs.items():
            self.output_values[name] = value
            self.parameter_values[name] = str(value)

    @Slot()
    def _refresh_analysis_status(self):
        if self.analysis_runner is None:
            return
        now = perf_counter()
        self.status_label.setText(
            f"{self._stage_phase} [{self._stage_position}/{self._stage_total}] {self._stage_title}"
            f"｜本項 {now - self._stage_started_at:.1f} 秒｜總計 {now - self._run_started_at:.1f} 秒"
        )

    @Slot()
    def _analysis_finished(self):
        runner = self.analysis_runner
        self.progress_timer.stop()
        self.analysis_runner = None
        self.run_button.setEnabled(True)
        self.run_selected_button.setEnabled(self.active_node_id is not None)
        self.csv_button.setEnabled(True)
        self.parameter_scroll.setEnabled(True)
        if runner.error:
            self.status_label.setText(f"分析中止：{runner.error}")
        else:
            self.status_label.setText(
                f"完成 {runner.completed_count}/{len(runner.rows)} 項分析，耗時 {runner.elapsed:.2f} 秒。結果已儲存。"
            )
        runner.deleteLater()
        if runner.error:
            QMessageBox.critical(self, "分析執行失敗", runner.error)

    def save_result(self, row, parameters, outputs, figure, details=None):
        save_analysis_result(RESULTS_DIR, row["node_id"], parameters,
                             details if details is not None else AnalysisResult(figure, outputs))

    def show_result(self, node_id):
        opened_at = perf_counter()
        timings = {"node_id": node_id,
                   "event_wait_ms": getattr(self, "_result_request_delay_ms", None)}
        node_dir = RESULTS_DIR / node_id
        if not (node_dir / "result.csv").exists():
            QMessageBox.information(self, "尚無分析結果", f"{node_id} 尚無已儲存結果，請先按「Run 全流程」。")
            return

        result_dir = node_dir
        dialog = ResultDialog(self)
        dialog.setWindowTitle(f"{node_id} 分析結果")
        dialog.resize(1300, 800)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(f"結果資料夾：{result_dir}"))

        splitter = QSplitter(Qt.Orientation.Horizontal)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        image_label = ScalableImageLabel()
        stage_started = perf_counter()
        image_label.set_image(result_dir / "plot.png")
        timings["image_ms"] = (perf_counter()-stage_started)*1000
        plot_selector = QComboBox()
        for title, filename in load_plot_choices(result_dir):
            plot_selector.addItem(title, filename)
        plot_selector.currentIndexChanged.connect(
            lambda: image_label.set_image(result_dir / plot_selector.currentData())
        )
        left_layout.addWidget(plot_selector)
        left_layout.addWidget(image_label, 3)
        left_layout.addWidget(QLabel("本次分析參數與結果"))
        table = QTableWidget(0, 3)
        table.horizontalHeader().setStretchLastSection(True)

        def display_table(filename):
            stage_started = perf_counter()
            with (result_dir / filename).open("r", newline="", encoding="utf-8-sig") as result_file:
                reader = csv.reader(result_file)
                headers = next(reader, [])
                table.setRowCount(0)
                table.setColumnCount(len(headers))
                table.setHorizontalHeaderLabels(headers)
                for record in reader:
                    row_index = table.rowCount()
                    table.insertRow(row_index)
                    for column, cell in enumerate(record):
                        table.setItem(row_index, column, QTableWidgetItem(cell))
            timings.setdefault("table_ms", (perf_counter()-stage_started)*1000)

        table_selector = QComboBox()
        table_selector.addItem("輸入參數與主要輸出", "result.csv")
        for path in sorted(result_dir.glob("*.csv")):
            if path.name != "result.csv":
                table_selector.addItem(path.stem, path.name)
        table_selector.currentIndexChanged.connect(lambda: display_table(table_selector.currentData()))
        display_table("result.csv")
        left_layout.addWidget(table_selector)
        left_layout.addWidget(table, 2)

        markdown_view = MarkdownView()
        markdown_path = result_dir / "analysis.md"
        stage_started = perf_counter()
        cache_info = {}
        if markdown_path.exists():
            markdown_html = render_markdown_file(markdown_path, cache_info=cache_info)
        else:
            markdown_html = render_markdown(
                f"# {node_id}\n\n尚未建立此分析的 Markdown 說明文件。"
            )
        markdown_view.setHtml(markdown_html)
        timings["notes_ms"] = (perf_counter()-stage_started)*1000
        timings["notes_cache_hit"] = cache_info.get("cache_hit")
        splitter.addWidget(left_panel)
        splitter.addWidget(markdown_view)
        splitter.setSizes([620, 620])
        layout.addWidget(splitter, 1)
        timings["prepare_ms"] = (perf_counter()-opened_at)*1000

        def report_first_frame():
            timings["first_frame_ms"] = (perf_counter()-opened_at)*1000
            self._last_result_open_timings = dict(timings)
            console = getattr(self, "console", None)
            if console is not None:
                event_wait = timings["event_wait_ms"]
                wait_text = f"{event_wait/1000:.3f} 秒" if event_wait is not None else "未記錄"
                cache_text = "快取命中" if timings["notes_cache_hit"] else "重新排版"
                console.append(
                    f"[開啟結果] {node_id}｜事件等待 {wait_text}"
                    f"｜圖片 {timings['image_ms']/1000:.3f} 秒"
                    f"｜表格 {timings['table_ms']/1000:.3f} 秒"
                    f"｜說明 {timings['notes_ms']/1000:.3f} 秒（{cache_text}）"
                    f"｜至首次顯示 {timings['first_frame_ms']/1000:.3f} 秒"
                )

        dialog.firstFrameReady.connect(report_first_frame)
        dialog.exec()

    def closeEvent(self, event):
        if self.analysis_runner is not None:
            self.status_label.setText("分析仍在執行，完成後即可關閉視窗。")
            event.ignore()
            return
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with LAST_SET_CSV.open("w", newline="", encoding="utf-8-sig") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(["name", "number"])
                writer.writerows(self.parameter_values.items())
        except OSError as error:
            QMessageBox.critical(self, "設定存檔失敗", str(error))
            event.ignore()
            return
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
