import csv
import io
import json
import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PySide6.QtCore import QTimer, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from analysis_data import load_analysis_parameters, parse_analysis_parameters
from document_theme import document_colors
from markdown_renderer import render_markdown
from markdown_view import MarkdownView
from plugin_loader import scan_analysis

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"
DEFAULT_CSV = DATA_DIR / "analysis_parameters.csv"
FLOW_CSV = DATA_DIR / "analysis_flow.csv"
LAST_SET_CSV = DATA_DIR / "analysis_parameters_last_set.csv"
RESULTS_DIR = DATA_DIR / "results"


class RedirectText(io.StringIO):
    def __init__(self, textbox):
        super().__init__()
        self.textbox = textbox

    def write(self, string):
        if string.strip():
            self.textbox.append(string.rstrip())

    def flush(self):
        pass


class FlowDiagramPage(QWebEnginePage):
    flowNodeRequested = Signal(str, bool)

    def acceptNavigationRequest(self, url, navigation_type, is_main_frame):
        if url.scheme() == "flow-node":
            node_id = url.path().strip("/")
            is_double_click = url.host() == "double"
            QTimer.singleShot(
                0,
                lambda: self.flowNodeRequested.emit(node_id, is_double_click),
            )
            return False
        return super().acceptNavigationRequest(url, navigation_type, is_main_frame)


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

        self.csv_button = QPushButton("選擇參數 CSV")
        self.csv_label = QLabel()
        self.csv_label.setWordWrap(True)
        self.database_button = QPushButton("檢視目前變量")
        self.run_button = QPushButton("Run 全流程")
        self.run_selected_button = QPushButton("單獨執行所選分析")
        self.run_selected_button.setEnabled(False)
        self.status_label = QLabel("選擇 CSV 後按 Run，依流程順序執行分析。")

        self.flow_view = QWebEngineView()
        self.flow_view.setMinimumHeight(210)
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
        self.parameter_title = QLabel("輸入參數（單擊流程節點以設定）")
        self.console = QTextEdit()
        self.console.setReadOnly(True)

        controls = QHBoxLayout()
        controls.addWidget(self.csv_button)
        controls.addWidget(self.database_button)
        controls.addWidget(self.csv_label, 1)
        controls.addWidget(self.run_button)
        controls.addWidget(self.run_selected_button)

        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addWidget(QLabel("單擊節點設定參數；雙擊查看結果；也可單獨執行所選分析（必要時會先跑前置分析）"))
        layout.addWidget(self.flow_view, 2)
        layout.addWidget(self.status_label)
        layout.addWidget(self.parameter_title)
        layout.addWidget(self.parameter_panel)
        layout.addWidget(self.console, 1)

        self.csv_button.clicked.connect(self.select_csv)
        self.database_button.clicked.connect(self.show_database)
        self.run_button.clicked.connect(self.run_flow)
        self.run_selected_button.clicked.connect(self.run_selected_analysis)

        self.load_csv(DEFAULT_CSV)
        QTimer.singleShot(0, self.select_csv)

    def load_flow(self):
        try:
            with FLOW_CSV.open("r", newline="", encoding="utf-8-sig") as flow_file:
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

    def build_flow_buttons(self):
        graph_ids = {
            row["node_id"]: f"flow_node_{index}"
            for index, row in enumerate(self.flow)
        }
        lines = ["graph TD"]
        main_rows = [row for row in self.flow if row["flow_row"] == "main"]
        branch_rows = [row for row in self.flow if row["flow_row"] == "branch"]
        secondary_rows = [row for row in self.flow if row["flow_row"] == "secondary"]
        tertiary_rows = [row for row in self.flow if row["flow_row"] == "tertiary"]
        merge_rows = [row for row in self.flow if row["flow_row"] == "merge"]

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

        for row in self.flow:
            graph_id = graph_ids[row["node_id"]]
            title = row["title"].replace('"', "&quot;")
            lines.append(f'    {graph_id}["{title}"]')

        diagram_markdown = "```mermaid\n" + "\n".join(lines) + "\n```"
        rendered_html = render_markdown(diagram_markdown)
        click_map = {
            row["title"]: row["node_id"]
            for row in self.flow
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
  function request(nodeId, kind) {{
    window.location.href = 'flow-node://' + kind + '/' + encodeURIComponent(nodeId);
  }}
  document.addEventListener('click', event => {{
    const nodeId = findNode(event);
    if (!nodeId) return;
    clearTimeout(clickTimer);
    clickTimer = setTimeout(() => request(nodeId, 'single'), 260);
  }});
  document.addEventListener('dblclick', event => {{
    const nodeId = findNode(event);
    if (!nodeId) return;
    clearTimeout(clickTimer);
    request(nodeId, 'double');
  }});
}})();
</script>"""
        rendered_html = rendered_html.replace("</body>", click_script + "</body>")
        self.flow_view.setHtml(rendered_html)

    def handle_flow_node_request(self, node_id, is_double_click):
        if is_double_click:
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
        self.parameter_values = dict(parameters)
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

        self.console.clear()
        self.status_label.setText("流程執行中…")
        self.run_button.setEnabled(False)
        self.run_selected_button.setEnabled(False)
        old_stdout = sys.stdout
        sys.stdout = RedirectText(self.console)
        try:
            for position, row in enumerate(self.flow, start=1):
                plugin = self.plugins_by_id[row["analysis_id"]]
                parameters = parse_analysis_parameters(self.parameter_values, plugin.parameters)
                print(f"[{position}/{len(self.flow)}] {row['title']}")
                result = plugin.run(parameters)
                if isinstance(result, tuple) and len(result) == 2:
                    fig, outputs = result
                else:
                    fig, outputs = result, {}
                self.save_result(row, parameters, outputs, fig)
                for name, value in outputs.items():
                    self.output_values[name] = value
                    self.parameter_values[name] = str(value)
                plt.close(fig)

            self.status_label.setText("完成。各分析結果已覆寫至 data/results/<節點>/。")
        except Exception as error:
            self.status_label.setText(f"流程中止：{error}")
            QMessageBox.critical(self, "流程執行失敗", str(error))
        finally:
            sys.stdout = old_stdout
            self.run_button.setEnabled(True)
            self.run_selected_button.setEnabled(self.active_node_id is not None)

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
            for parameter_name in plugin.parameters:
                current_value = self.parameter_values.get(parameter_name)
                if current_value is not None and str(current_value).strip():
                    continue
                producer_row = producer_by_output.get(parameter_name)
                if producer_row is None:
                    raise ValueError(f"{row['title']} 缺少輸入參數：{parameter_name}")
                include_dependencies(producer_row)
            visiting.remove(node_id)
            required_node_ids.add(node_id)

        include_dependencies(selected_row)
        return [row for row in self.flow if row["node_id"] in required_node_ids]

    def run_selected_analysis(self):
        if not self.active_node_id:
            QMessageBox.information(self, "尚未選擇分析", "請先單擊流程圖中的分析節點。")
            return

        try:
            selected_rows = self._required_analysis_rows(self.active_node_id)
        except ValueError as error:
            self.status_label.setText(f"無法執行所選分析：{error}")
            QMessageBox.warning(self, "分析參數錯誤", str(error))
            return

        selected_row = next(
            row for row in self.flow if row["node_id"] == self.active_node_id
        )
        self.console.clear()
        self.status_label.setText(f"執行所選分析：{selected_row['title']}…")
        self.run_button.setEnabled(False)
        self.run_selected_button.setEnabled(False)
        old_stdout = sys.stdout
        sys.stdout = RedirectText(self.console)
        try:
            for position, row in enumerate(selected_rows, start=1):
                plugin = self.plugins_by_id[row["analysis_id"]]
                parameters = parse_analysis_parameters(
                    self.parameter_values,
                    plugin.parameters,
                )
                if row["node_id"] == self.active_node_id:
                    print(f"[{position}/{len(selected_rows)}] 所選分析：{row['title']}")
                else:
                    print(f"[{position}/{len(selected_rows)}] 必要前置分析：{row['title']}")
                result = plugin.run(parameters)
                if isinstance(result, tuple) and len(result) == 2:
                    figure, outputs = result
                else:
                    figure, outputs = result, {}
                self.save_result(row, parameters, outputs, figure)
                for name, value in outputs.items():
                    self.output_values[name] = value
                    self.parameter_values[name] = str(value)
                plt.close(figure)
            self.status_label.setText(
                f"完成：{selected_row['title']} 分析結果已儲存。"
            )
        except Exception as error:
            self.status_label.setText(f"所選分析執行失敗：{error}")
            QMessageBox.critical(self, "分析執行失敗", str(error))
        finally:
            sys.stdout = old_stdout
            self.run_button.setEnabled(True)
            self.run_selected_button.setEnabled(self.active_node_id is not None)

    def save_result(self, row, parameters, outputs, figure):
        result_dir = RESULTS_DIR / row["node_id"]
        result_dir.mkdir(parents=True, exist_ok=True)
        figure.savefig(result_dir / "plot.png", dpi=300, bbox_inches="tight")
        with (result_dir / "result.csv").open("w", newline="", encoding="utf-8-sig") as result_file:
            writer = csv.writer(result_file)
            writer.writerow(["category", "name", "number"])
            writer.writerows(("輸入量", name, value) for name, value in parameters.items())
            writer.writerows(("導出量", name, value) for name, value in outputs.items())

    def show_result(self, node_id):
        node_dir = RESULTS_DIR / node_id
        if not (node_dir / "result.csv").exists():
            QMessageBox.information(self, "尚無分析結果", f"{node_id} 尚無已儲存結果，請先按「Run 全流程」。")
            return

        result_dir = node_dir
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{node_id} 分析結果")
        dialog.resize(1300, 800)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(f"結果資料夾：{result_dir}"))

        splitter = QSplitter(Qt.Orientation.Horizontal)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        image_label = ScalableImageLabel()
        image_label.set_image(result_dir / "plot.png")
        left_layout.addWidget(image_label, 3)
        left_layout.addWidget(QLabel("本次分析參數與結果"))
        table = QTableWidget(0, 3)
        table.setHorizontalHeaderLabels(["類別", "變量名稱", "數值"])
        table.horizontalHeader().setStretchLastSection(True)
        with (result_dir / "result.csv").open("r", newline="", encoding="utf-8-sig") as result_file:
            for record in csv.DictReader(result_file):
                self.add_variable_row(table, record["category"], record["name"], record["number"])
        left_layout.addWidget(table, 2)

        markdown_view = MarkdownView()
        markdown_path = result_dir / "analysis.md"
        if markdown_path.exists():
            markdown_html = render_markdown(markdown_path.read_text(encoding="utf-8"))
        else:
            markdown_html = render_markdown(
                f"# {node_id}\n\n尚未建立此分析的 Markdown 說明文件。"
            )
        markdown_view.setHtml(markdown_html)
        splitter.addWidget(left_panel)
        splitter.addWidget(markdown_view)
        splitter.setSizes([620, 620])
        layout.addWidget(splitter, 1)

        dialog.exec()

    def closeEvent(self, event):
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
