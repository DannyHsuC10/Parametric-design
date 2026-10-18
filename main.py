import csv
import io
import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QPixmap
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
    QScrollArea,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from analysis_data import load_analysis_parameters, parse_analysis_parameters
from markdown_renderer import render_markdown
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


class FlowNodeButton(QPushButton):
    singleClicked = Signal()
    doubleClicked = Signal()

    def __init__(self, text):
        super().__init__(text)
        self._suppress_click = False
        self._single_click_timer = QTimer(self)
        self._single_click_timer.setSingleShot(True)
        self._single_click_timer.setInterval(250)
        self._single_click_timer.timeout.connect(self.singleClicked.emit)
        self._suppress_reset_timer = QTimer(self)
        self._suppress_reset_timer.setSingleShot(True)
        self._suppress_reset_timer.setInterval(400)
        self._suppress_reset_timer.timeout.connect(self.clear_click_suppression)
        self.clicked.connect(self.schedule_single_click)

    def schedule_single_click(self):
        if self._suppress_click:
            self._suppress_click = False
            self._suppress_reset_timer.stop()
            return
        self._single_click_timer.start()

    def mouseDoubleClickEvent(self, event):
        self._single_click_timer.stop()
        self._suppress_click = True
        self._suppress_reset_timer.start()
        self.doubleClicked.emit()
        event.accept()

    def clear_click_suppression(self):
        self._suppress_click = False


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
            self.setPixmap(self.original_pixmap.scaled(
                self.size(), Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
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
        self.result_buttons = {}
        self.active_node_id = None
        self.plot = None

        self.csv_button = QPushButton("選擇參數 CSV")
        self.csv_label = QLabel()
        self.csv_label.setWordWrap(True)
        self.database_button = QPushButton("檢視目前變量")
        self.run_button = QPushButton("Run 全流程")
        self.status_label = QLabel("選擇 CSV 後按 Run，依流程順序執行分析。")

        self.flow_widget = QWidget()
        self.flow_layout = QHBoxLayout(self.flow_widget)
        self.flow_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.build_flow_buttons()
        self.flow_scroll = QScrollArea()
        self.flow_scroll.setWidgetResizable(True)
        self.flow_scroll.setWidget(self.flow_widget)
        self.flow_scroll.setMinimumHeight(150)

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

        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addWidget(QLabel("分析流程（單擊節點設定參數；雙擊節點查看最近一次已儲存結果）"))
        layout.addWidget(self.flow_scroll, 2)
        layout.addWidget(self.status_label)
        layout.addWidget(self.parameter_title)
        layout.addWidget(self.parameter_panel)
        layout.addWidget(self.console, 1)

        self.csv_button.clicked.connect(self.select_csv)
        self.database_button.clicked.connect(self.show_database)
        self.run_button.clicked.connect(self.run_flow)

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
                node_id = row["node_id"].strip()
                analysis_id = row["analysis_id"].strip()
                if not re.fullmatch(r"[A-Za-z0-9_-]+", node_id):
                    raise ValueError(f"無效的節點名稱：{node_id}")
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
            return rows
        except (KeyError, ValueError) as error:
            QMessageBox.critical(self, "流程設定錯誤", str(error))
            return []

    def build_flow_buttons(self):
        for index, row in enumerate(self.flow):
            button = FlowNodeButton(row["title"])
            button.setMinimumSize(140, 72)
            button.setToolTip("單擊：設定參數；雙擊：開啟最近一次已儲存結果")
            button.singleClicked.connect(
                lambda node=row["node_id"]: self.show_node_parameters(node)
            )
            button.doubleClicked.connect(
                lambda node=row["node_id"]: self.show_result(node)
            )
            self.result_buttons[row["node_id"]] = button
            self.flow_layout.addWidget(button)
            if index < len(self.flow) - 1:
                arrow = QLabel("→")
                arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
                arrow.setStyleSheet("font-size: 28px; color: #647184;")
                self.flow_layout.addWidget(arrow)
        self.flow_layout.addStretch(1)

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
            edit = QLineEdit(self.parameter_values.get(name, ""))
            edit.textChanged.connect(lambda value, key=name: self.update_parameter(key, value))
            self.parameter_form.addRow(name, edit)
            self.parameter_edits[name] = edit

    def show_node_parameters(self, node_id):
        row = next((item for item in self.flow if item["node_id"] == node_id), None)
        if row is None:
            return
        self.active_node_id = node_id
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
        close_button = QPushButton("關閉")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
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

        self.console.clear()
        self.status_label.setText("流程執行中…")
        self.run_button.setEnabled(False)
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

    def save_result(self, row, parameters, outputs, figure):
        result_dir = RESULTS_DIR / row["node_id"]
        result_dir.mkdir(parents=True, exist_ok=True)
        figure.savefig(result_dir / "plot.png", dpi=140, bbox_inches="tight")
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

        markdown_view = QTextBrowser()
        markdown_path = result_dir / "analysis.md"
        if markdown_path.exists():
            markdown_view.setHtml(render_markdown(markdown_path.read_text(encoding="utf-8")))
        else:
            markdown_view.setHtml(render_markdown(f"# {node_id}\n\n尚未建立此分析的 Markdown 說明文件。"))
        splitter.addWidget(left_panel)
        splitter.addWidget(markdown_view)
        splitter.setSizes([620, 620])
        layout.addWidget(splitter, 1)

        close_button = QPushButton("關閉")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
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


app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
