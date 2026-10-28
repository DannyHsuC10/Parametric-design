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
    QCheckBox,
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
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.analysis_data import canonical_parameter_name, load_analysis_parameters, parse_analysis_parameters
from app.analysis_cache import saved_outputs
from app.analysis_result import AnalysisResult, load_plot_choices, save_analysis_result
from app.analysis_runner import AnalysisRunner
from app.analysis_settings import NodeSettings, load_node_settings, save_node_settings
from app.document_theme import document_colors
from app.flow_diagram import render_flow_diagram
from app.markdown_renderer import render_markdown, render_markdown_file
from app.markdown_view import MarkdownView
from app.plugin_loader import scan_analysis

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
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
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
        self.node_settings_path = LAST_SET_CSV.with_suffix(".nodes.json")
        settings_loaded = True
        try:
            self.node_settings = load_node_settings(self.node_settings_path)
        except (OSError, ValueError) as error:
            self.node_settings = {}
            settings_loaded = False
            QMessageBox.warning(self, "分析個別設定載入失敗", str(error))
        new_nodes = {row["node_id"] for row in self.flow} - self.node_settings.keys()
        for row in self.flow:
            self.node_settings.setdefault(row["node_id"], NodeSettings())
        if settings_loaded and (new_nodes or not self.node_settings_path.exists()):
            self._save_node_settings()
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
        self.run_selected_button = QPushButton("只執行所選分析")
        self.run_selected_button.setToolTip("只重算所選節點，沿用最近一次成功的上游結果（含已儲存結果）。")
        self.run_selected_button.setEnabled(False)
        self.run_with_dependencies_button = QPushButton("所選分析＋前置分析")
        self.run_with_dependencies_button.setToolTip("重算所選節點；前置分析只重算輸入／來源資料有變更或尚無成功結果的項目。")
        self.run_with_dependencies_button.setEnabled(False)
        self.run_affected_button = QPushButton("執行所有受影響分析")
        self.run_affected_button.setToolTip("跨所有流程依序更新輸入或來源資料已變更、或尚無結果的分析，其餘沿用成功結果。")
        self.status_label = QLabel("選擇 CSV 後按 Run，依流程順序執行分析。")

        self.flow_selector = QComboBox()
        self.flow_selector.setMinimumWidth(220)
        self.flow_selector.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.flow_stack = QStackedWidget()
        self.flow_stack.setMinimumHeight(120)
        self.flow_views = {}
        self.flow_pages = {}
        groups = list(dict.fromkeys(row.get("flow_group", "") for row in self.flow))
        self.flow_groups = [None] + [group for group in groups if group]
        for group in self.flow_groups:
            title = "完整流程" if group is None else group
            page = QWidget()
            page_layout = QVBoxLayout(page)
            page_layout.setContentsMargins(0, 0, 0, 0)
            self.flow_stack.addWidget(page)
            self.flow_selector.addItem(title)
        self.flow_selector.currentIndexChanged.connect(self.show_flow_page)
        self.show_flow_page(0)

        self.parameter_form = QFormLayout()
        self.parameter_panel = QWidget()
        self.parameter_panel.setLayout(self.parameter_form)
        self.parameter_scroll = QScrollArea()
        self.parameter_scroll.setWidgetResizable(True)
        self.parameter_scroll.setWidget(self.parameter_panel)
        self.parameter_scroll.setMinimumHeight(120)
        self.parameter_title = QLabel("輸入參數（單擊流程節點以設定）")
        self.skip_analysis_checkbox = QCheckBox("跳過此分析（所有執行按鈕皆適用）")
        self.skip_analysis_checkbox.setToolTip("不執行此分析，也不因相依需求重跑它；保留既有結果供後續分析沿用。")
        self.nonessential_analysis_checkbox = QCheckBox("非必要分析")
        self.nonessential_analysis_checkbox.setToolTip("僅讓流程圖方塊變淡，不影響執行；只有勾選「跳過此分析」才會跳過。")
        self.manual_parameters_checkbox = QCheckBox("不套用前置分析結果，全部參數手動設定")
        self.manual_parameters_checkbox.setToolTip("顯示全部輸入參數；數值只儲存在此分析，不會改寫共用參數或前置結果。")
        self.parameter_options = QWidget()
        options_layout = QVBoxLayout(self.parameter_options)
        options_layout.setContentsMargins(0, 0, 0, 0)
        options_layout.addWidget(self.skip_analysis_checkbox)
        options_layout.addWidget(self.nonessential_analysis_checkbox)
        options_layout.addWidget(self.manual_parameters_checkbox)
        self.parameter_options.setEnabled(False)
        self.skip_analysis_checkbox.toggled.connect(self.set_analysis_skipped)
        self.nonessential_analysis_checkbox.toggled.connect(self.set_analysis_nonessential)
        self.manual_parameters_checkbox.toggled.connect(self.set_manual_parameters)
        self.console = QTextEdit()
        self.console.setReadOnly(True)

        controls = QHBoxLayout()
        controls.addWidget(self.csv_button)
        controls.addWidget(self.database_button)
        controls.addWidget(self.csv_label, 1)
        controls.addWidget(self.run_button)
        controls.addWidget(self.run_selected_button)
        controls.addWidget(self.run_with_dependencies_button)
        controls.addWidget(self.run_affected_button)

        parameter_section = QWidget()
        parameter_layout = QVBoxLayout(parameter_section)
        parameter_layout.setContentsMargins(0, 0, 0, 0)
        parameter_layout.addWidget(self.parameter_title)
        parameter_layout.addWidget(self.parameter_options)
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
        flow_controls = QHBoxLayout()
        flow_controls.addWidget(QLabel("選擇流程"))
        flow_controls.addWidget(self.flow_selector)
        flow_controls.addStretch(1)
        flow_layout.addLayout(flow_controls)
        flow_layout.addWidget(self.flow_stack, 1)
        flow_layout.addWidget(self.status_label)

        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setHandleWidth(8)
        self.main_splitter.addWidget(flow_section)
        self.main_splitter.addWidget(self.work_splitter)
        self.main_splitter.setStretchFactor(0, 4)
        self.main_splitter.setStretchFactor(1, 4)
        self.main_splitter.handle(1).setToolTip("上下拖曳，調整流程圖與下方工作區高度")

        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        execution_hint = QLabel("單擊節點設定參數；雙擊查看結果。前置分析會略過未變更的項目；「執行所有受影響分析」可跨流程更新。")
        execution_hint.setWordWrap(True)
        layout.addWidget(execution_hint)
        layout.addWidget(self.main_splitter, 1)

        self.csv_button.clicked.connect(self.select_csv)
        self.database_button.clicked.connect(self.show_database)
        self.run_button.clicked.connect(self.run_flow)
        self.run_selected_button.clicked.connect(self.run_selected_analysis)
        self.run_with_dependencies_button.clicked.connect(self.run_selected_with_dependencies)
        self.run_affected_button.clicked.connect(self.run_affected_analyses)

        self.load_csv(DEFAULT_CSV)
        # Open the source node's editable geometry inputs immediately.
        self.show_node_parameters("cog_movable")
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
                row.setdefault("extra_from", "")
                row["flow_group"] = (row.get("flow_group") or "").strip()
                row["merge_from"] = (row.get("merge_from") or "").strip()
                row["extra_from"] = (row.get("extra_from") or "").strip()
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
            for row in rows:
                extra_sources = [source.strip() for source in row["extra_from"].split("|") if source.strip()]
                for source in extra_sources:
                    if source not in node_ids:
                        raise ValueError(f"額外連線的來源不存在：{source}")
                row["extra_from"] = "|".join(extra_sources)
            return rows
        except (KeyError, ValueError) as error:
            QMessageBox.critical(self, "流程設定錯誤", str(error))
            return []

    def show_flow_page(self, index):
        if not 0 <= index < self.flow_stack.count():
            return
        self.flow_stack.setCurrentIndex(index)
        if index in self.flow_views:
            return
        view = QWebEngineView()
        view.setMinimumHeight(120)
        page = FlowDiagramPage(view)
        page.setBackgroundColor(QColor(document_colors()["background"]))
        view.setPage(page)
        view.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        page.flowNodeRequested.connect(
            lambda node_id, double, source=page: self.handle_flow_node_request(node_id, double, source)
        )
        page.loadFinished.connect(lambda loaded, source=page: self._sync_flow_state(source) if loaded else None)
        self.flow_views[index] = view
        self.flow_pages[index] = page
        self.flow_stack.widget(index).layout().addWidget(view)
        if index == 0:
            self.flow_view, self.flow_page = view, page
        self.build_flow_buttons(view=view, group=self.flow_groups[index])

    def build_flow_buttons(self, flow=None, view=None, group=None):
        flow = self.flow if flow is None else flow
        view = self.flow_view if view is None else view
        view.setHtml(render_flow_diagram(flow, group))

    def _sync_flow_state(self, page=None):
        skipped = [node_id for node_id, options in self.node_settings.items() if options.skip]
        nonessential = [node_id for node_id, options in self.node_settings.items() if options.nonessential]
        script = ("if (window.flowSelection) { window.flowSelection.select("
                  + json.dumps(self.active_node_id) + "); window.flowSelection.setSkipped("
                  + json.dumps(skipped) + "); window.flowSelection.setNonessential("
                  + json.dumps(nonessential) + "); }")
        for target in ([page] if page is not None else self.flow_pages.values()):
            target.runJavaScript(script)

    def handle_flow_node_request(self, node_id, is_double_click, source_page=None):
        if self.analysis_runner is not None:
            self._sync_flow_state()
            return
        self.show_node_parameters(node_id)
        if is_double_click:
            self._result_request_delay_ms = getattr(source_page or self.flow_page, "last_request_delay_ms", None)
            self.show_result(node_id)

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
        # Outputs are restored by execution actions, never taken from the input CSV.
        self.parameter_values = {name: value for name, value in (defaults | parameters).items()
                                 if name not in self.output_names}
        self.output_values = {}
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
        node_id = getattr(self, "active_node_id", None)
        options = getattr(self, "node_settings", {}).get(node_id, NodeSettings())
        for name in plugin.parameters:
            if not options.manual and (name in plugin.hidden_parameters or name in {
                "ms", "mu", "mu_front", "mu_rear", "L", "hl_front_weight_ratio",
                "hl_sprung_roll_inertia_kg_m2",
                "mu_w", "wl_mu_y",
            }) and name not in plugin.visible_parameters:
                continue
            values = options.parameters if options.manual else self.parameter_values
            edit = QLineEdit(str(values.get(name, "")))
            if options.manual:
                edit.setPlaceholderText("請輸入此分析專用的參數")
                edit.textChanged.connect(
                    lambda value, key=name, node=node_id: self.update_manual_parameter(node, key, value))
            elif name in self.output_names:
                edit.setReadOnly(True)
                edit.setPlaceholderText("由前置分析計算")
                edit.setToolTip("沿用最近一次的上游結果；修改來源資料後，請使用「所選分析＋前置分析」更新。")
            else:
                edit.textChanged.connect(lambda value, key=name: self.update_parameter(key, value))
            labels = {
                "ms": "全車簧上質量 ms（kg）",
                "mu": "平均單輪簧下質量 mu（kg）",
                "mu_front": "前軸單輪簧下質量（kg）",
                "mu_rear": "後軸單輪簧下質量（kg）",
                "hl_front_weight_ratio": "全車前軸重量比（0～1）",
                "hl_sprung_roll_inertia_kg_m2": "簧上側傾慣量（kg·m²）",
                "h_cog": "重心高度 h_cog（m）",
                "Kt": "輪胎垂直剛性 Kt（N/m）",
                "ct": "輪胎阻尼 ct（N·s/m）",
                "MR": "懸吊運動比 MR",
                "t": "輪距 t（m）",
                "L": "軸距 L（m）",
                "hl_rear_heave_spring_ratio": "後軸 Heave 剛性比",
                "hl_rear_roll_spring_ratio": "後軸 Roll 剛性比",
                "full_body_twist_stiffness_Nm_per_rad": "車架扭轉剛性（N·m/rad）",
                "cog_total_Ixx_kg_m2": "全車 Roll 慣量 Ixx（kg·m²，COG）",
                "cog_total_Iyy_kg_m2": "全車 Pitch 慣量 Iyy（kg·m²，COG）",
                "cog_total_Izz_kg_m2": "全車 Yaw 慣量 Izz（kg·m²，COG）",
                "h_rc": "Roll Center 高度 h_rc（m）",
                "tau_rc": "Roll Center 傳遞時間常數 tau_rc（s）",
                "k_frame_to_roll_ratio": "車架／Roll 剛性比",
                "m_frame": "等效車架質量 m_frame（kg）",
                "zeta_frame": "車架阻尼比",
                "k_left": "左角點附加彈簧剛性（N/m）",
                "k_right": "右角點附加彈簧剛性（N/m）",
                "Iy": "簧上俯仰慣量 Iy（kg·m²）",
                "anti_dive_front": "前軸 Anti-dive 比例",
                "anti_squat_rear": "後軸 Anti-squat 比例",
                "k_front": "前軸附加角點彈簧剛性（N/m）",
                "k_rear": "後軸附加角點彈簧剛性（N/m）",
                "drive_motor_torque_Nm": "馬達最大扭矩（N·m，motor）",
                "cog_front_axle_x_m": "前軸輪心 x（m）",
                "cog_rear_axle_x_m": "後軸輪心 x（m）",
                "bicycle_front_cornering_stiffness_N_per_rad": "前軸側偏剛性 Cf（N/rad）",
                "bicycle_rear_cornering_stiffness_N_per_rad": "後軸側偏剛性 Cr（N/rad）",
                "bicycle_v_ref_kmh": "v_ref（km/h）",
                "vehicle_max_steering_angle_deg": "車輛最大轉向角（deg）",
                "brake_driver_force_N": "車手踏力（N）",
                "brake_balance_bar_front_ratio": "Balance bar 前總泵推力比例（0～1）",
                "brake_master_front_diameter_m": "前總泵缸徑（m）",
                "brake_master_rear_diameter_m": "後總泵缸徑（m）",
                "brake_caliper_front_piston_diameter_m": "前卡鉗活塞直徑（m）",
                "brake_caliper_rear_piston_diameter_m": "後卡鉗活塞直徑（m）",
                "brake_caliper_front_piston_count": "每顆前卡鉗兩側總活塞數（正偶數）",
                "brake_caliper_rear_piston_count": "每顆後卡鉗兩側總活塞數（正偶數）",
                "brake_pad_mu": "來令片摩擦係數",
                "brake_disc_outer_diameter_m": "碟盤外徑（m）",
                "brake_disc_contact_offset_m": "碟盤外緣至有效摩擦點的徑向距離（m）",
                "brake_safety_factor": "踏板比設計安全係數（至少 1）",
                "rc_chassis_stiffness_ratio": "車架／懸吊等效線性剛性比",
            }
            self.parameter_form.addRow(labels.get(name, name), edit)
            if name == "drive_motor_torque_Nm":
                edit.setToolTip("自動使用 motor 馬達曲線分析的 max(torque)。修改曲線 CSV 後，執行前置分析或所有受影響分析以更新。")
            if name in {"cog_front_axle_x_m", "cog_rear_axle_x_m"}:
                edit.setToolTip("手動輸入輪胎中心位置，座標基準為 Excel 原點；不使用 Excel 零件重心 dx。")
            if name == "vehicle_max_steering_angle_deg":
                edit.setToolTip("等效前輪轉角，非方向盤轉角；Turning_Radius 的標記角度也會用作 Bicycle_Model 的轉向階躍。須大於 0° 且小於 90°。")
            if name == "bicycle_v_ref_kmh":
                edit.setToolTip("Bicycle Model 的手動參考速度，須大於零；不會被 Skidpad 的計算速度覆蓋。")
            if name.startswith("brake_caliper_"):
                edit.setToolTip("假設對向固定式、等徑活塞卡鉗；活塞數包含單顆卡鉗的兩側，每軸為兩顆卡鉗。")
            if name == "brake_balance_bar_front_ratio":
                edit.setToolTip("前總泵分到的推力比例；實際前後煞車力比例另由總泵、卡鉗與碟盤參數計算。")
            if options.manual:
                edit.setToolTip("此數值僅作為本分析的輸入，不會改寫共用參數或其他分析的輸入設定。")
            self.parameter_edits[name] = edit

    def _save_node_settings(self):
        try:
            save_node_settings(self.node_settings_path, self.node_settings)
        except OSError as error:
            QMessageBox.warning(self, "分析個別設定存檔失敗",
                                f"本次變更尚未存入 JSON，請確認檔案可寫入。\n{error}")
            return False
        return True

    def set_analysis_skipped(self, checked):
        if self.active_node_id is not None:
            self.node_settings.setdefault(self.active_node_id, NodeSettings()).skip = checked
            self._sync_flow_state()
            self._save_node_settings()

    def set_analysis_nonessential(self, checked):
        if self.active_node_id is not None:
            self.node_settings.setdefault(self.active_node_id, NodeSettings()).nonessential = checked
            self._sync_flow_state()
            self._save_node_settings()

    def _manual_parameter_defaults(self, row, plugin):
        """Seed private inputs from available values without changing shared state."""
        values = dict(self.parameter_values)
        for producer_row in self.flow:
            if producer_row["node_id"] == row["node_id"]:
                continue
            producer = self.plugins_by_id[producer_row["analysis_id"]]
            missing = {name for name in plugin.parameters if not str(values.get(name, "")).strip()}
            if missing.intersection(producer.outputs):
                values.update({name: value for name, value in
                               saved_outputs(RESULTS_DIR, producer_row["node_id"], producer.outputs).items()
                               if name in missing})
        try:
            with (RESULTS_DIR / row["node_id"] / "result.csv").open(encoding="utf-8-sig", newline="") as stream:
                for entry in csv.DictReader(stream):
                    name = canonical_parameter_name(entry.get("name", ""))
                    if (entry.get("category") == "輸入量" and name in plugin.parameters
                            and not str(values.get(name, "")).strip()):
                        values[name] = entry.get("number") or ""
        except (OSError, UnicodeError, csv.Error):
            pass
        return {name: str(values.get(name, plugin.parameter_defaults.get(name, "")))
                for name in plugin.parameters}

    def set_manual_parameters(self, checked):
        if self.active_node_id is None:
            return
        row = next(row for row in self.flow if row["node_id"] == self.active_node_id)
        plugin = self.plugins_by_id[row["analysis_id"]]
        options = self.node_settings.setdefault(self.active_node_id, NodeSettings())
        if checked:
            for name, value in self._manual_parameter_defaults(row, plugin).items():
                options.parameters.setdefault(name, value)
        options.manual = checked
        self._save_node_settings()
        self.build_parameter_fields(plugin)

    def update_manual_parameter(self, node_id, name, value):
        self.node_settings.setdefault(node_id, NodeSettings()).parameters[canonical_parameter_name(name)] = value
        self._save_node_settings()

    def show_node_parameters(self, node_id):
        row = next((item for item in self.flow if item["node_id"] == node_id), None)
        if row is None:
            return
        self.active_node_id = node_id
        options = self.node_settings.get(node_id, NodeSettings())
        for checkbox, checked in ((self.skip_analysis_checkbox, options.skip),
                                  (self.nonessential_analysis_checkbox, options.nonessential),
                                  (self.manual_parameters_checkbox, options.manual)):
            checkbox.blockSignals(True)
            checkbox.setChecked(checked)
            checkbox.blockSignals(False)
        self.parameter_options.setEnabled(self.analysis_runner is None)
        self.run_selected_button.setEnabled(self.analysis_runner is None)
        self.run_with_dependencies_button.setEnabled(self.analysis_runner is None)
        plugin = self.plugins_by_id[row["analysis_id"]]
        self.parameter_title.setText(f"{row['title']} 輸入參數")
        self.build_parameter_fields(plugin)
        self._sync_flow_state()

    def update_parameter(self, name, value):
        name = canonical_parameter_name(name)
        self.parameter_values[name] = value
        # Retain the last successful upstream values for explicit single-node runs.
        # Incremental runs compare each node's actual inputs to its saved inputs.

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
        self._run_full_flow(incremental=False)

    def run_affected_analyses(self):
        self._run_full_flow(incremental=True)

    def _run_full_flow(self, incremental):
        if self.analysis_runner is not None:
            return
        if not self.flow:
            QMessageBox.warning(self, "沒有分析流程", "請檢查 data/analysis_flow.csv")
            return

        try:
            selected_rows = self._all_analysis_rows_in_dependency_order()
        except ValueError as error:
            self.status_label.setText(f"參數尚未完成：{error}")
            QMessageBox.warning(self, "參數錯誤", str(error))
            return

        self._start_analysis(selected_rows, incremental=incremental)
        if incremental:
            self.console.append("檢查所有流程：只重算輸入、來源資料已變更或尚無結果的分析；未變更的項目沿用成功結果。")

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
        ordered_rows = []

        def include_dependencies(row):
            node_id = row["node_id"]
            if node_id in required_node_ids:
                return
            if node_id in visiting:
                raise ValueError(f"分析依賴形成循環：{node_id}")
            visiting.add(node_id)
            plugin = self.plugins_by_id[row["analysis_id"]]
            options = getattr(self, "node_settings", {}).get(node_id, NodeSettings())
            if options.skip or options.manual:
                if options.manual and not options.skip:
                    try:
                        parse_analysis_parameters(options.parameters, plugin.parameters)
                    except ValueError as error:
                        raise ValueError(f"{row['title']} 手動參數未完成：{error}") from error
                visiting.remove(node_id)
                required_node_ids.add(node_id)
                ordered_rows.append(row)
                return
            for dependency in getattr(plugin, "required_analyses", ()):
                dependency_row = next((item for item in self.flow if item["node_id"] == dependency), None)
                if dependency_row is None:
                    raise ValueError(f"{row['title']} 找不到前置分析：{dependency}")
                include_dependencies(dependency_row)
            for parameter_name in plugin.parameters:
                current_value = self.parameter_values.get(parameter_name)
                producer_row = producer_by_output.get(parameter_name)
                if producer_row is not None:
                    include_dependencies(producer_row)
                elif current_value is None or not str(current_value).strip():
                    raise ValueError(f"{row['title']} 缺少輸入參數：{parameter_name}")
            visiting.remove(node_id)
            required_node_ids.add(node_id)
            ordered_rows.append(row)

        include_dependencies(selected_row)
        # Dependencies can appear after the selected model in the visual flow.
        # Preserve the DFS post-order so upstream derived outputs exist before
        # the consumer's parameters are parsed and its analysis is run.
        return ordered_rows

    def _all_analysis_rows_in_dependency_order(self):
        """Return the whole workflow with every producer before its consumers."""
        ordered_rows = []
        included = set()
        for row in self.flow:
            for required_row in MainWindow._required_analysis_rows(self, row["node_id"]):
                if required_row["node_id"] not in included:
                    included.add(required_row["node_id"])
                    ordered_rows.append(required_row)
        return ordered_rows

    def run_selected_analysis(self):
        self._run_selected(include_dependencies=False)

    def run_selected_with_dependencies(self):
        self._run_selected(include_dependencies=True)

    def _single_analysis_values(self, row):
        """Reuse live outputs first; restore missing inputs from their producer's export."""
        plugin = self.plugins_by_id[row["analysis_id"]]
        options = getattr(self, "node_settings", {}).get(row["node_id"], NodeSettings())
        if options.skip:
            return dict(self.parameter_values), {}
        if options.manual:
            parse_analysis_parameters(options.parameters, plugin.parameters)
            return dict(options.parameters), {}
        values = dict(self.parameter_values)
        restored = {}
        missing = {name for name in plugin.parameters if not str(values.get(name, "")).strip()}
        for producer_row in self.flow:
            if producer_row["node_id"] == row["node_id"]:
                continue
            producer = self.plugins_by_id[producer_row["analysis_id"]]
            needed = missing.intersection(producer.outputs)
            if not needed:
                continue
            restored.update({name: value for name, value in
                             saved_outputs(RESULTS_DIR, producer_row["node_id"], producer.outputs).items()
                             if name in needed})
        values.update(restored)
        missing = [name for name in plugin.parameters if not str(values.get(name, "")).strip()]
        if missing:
            raise ValueError(
                "缺少可沿用的參數或上游結果：" + ", ".join(missing)
                + "。請先執行「所選分析＋前置分析」。"
            )
        parse_analysis_parameters(values, plugin.parameters)
        return values, restored

    def _run_selected(self, include_dependencies):
        if self.analysis_runner is not None:
            return
        if not self.active_node_id:
            QMessageBox.information(self, "尚未選擇分析", "請先單擊流程圖中的分析節點。")
            return

        try:
            restored = {}
            if include_dependencies:
                selected_rows = self._required_analysis_rows(self.active_node_id)
            else:
                row = next((row for row in self.flow if row["node_id"] == self.active_node_id), None)
                if row is None:
                    raise ValueError("找不到所選分析節點")
                values, restored = self._single_analysis_values(row)
                selected_rows = [row]
        except ValueError as error:
            self.status_label.setText(f"無法執行所選分析：{error}")
            QMessageBox.warning(self, "分析參數錯誤", str(error))
            return

        manual = self.node_settings.get(self.active_node_id, NodeSettings()).manual
        if not include_dependencies and not manual:
            self.parameter_values.update(values)
            self.output_values.update(restored)
        self._start_analysis(selected_rows, self.active_node_id, incremental=include_dependencies)
        if self.node_settings.get(self.active_node_id, NodeSettings()).skip:
            self.console.append("所選分析已勾選跳過，不會執行或重跑其前置分析。")
        elif manual:
            self.console.append("所選分析使用此節點專用的手動輸入，不套用前置結果，也不改寫共用參數。")
        elif include_dependencies:
            self.console.append("重算所選分析；前置分析會逐項比對輸入與來源資料，略過未變更且已有成功結果的項目。")
        else:
            self.console.append("只執行所選分析：沿用最近一次成功的上游結果，上游不重算。")
            if restored:
                self.console.append("已從儲存結果載入：" + ", ".join(restored))

    def _start_analysis(self, rows, selected_node_id=None, *, incremental=False):
        self.console.clear()
        self.run_button.setEnabled(False)
        self.run_selected_button.setEnabled(False)
        self.run_with_dependencies_button.setEnabled(False)
        self.run_affected_button.setEnabled(False)
        self.csv_button.setEnabled(False)
        self.parameter_scroll.setEnabled(False)
        self.parameter_options.setEnabled(False)
        self._run_started_at = perf_counter()
        self._stage_started_at = self._run_started_at
        self._stage_position = 0
        self._stage_total = len(rows)
        self._stage_title = "準備分析"
        self._stage_phase = "準備中"
        runner = AnalysisRunner(self.plugins_by_id, rows, self.parameter_values, RESULTS_DIR,
                                selected_node_id, parent=self, incremental=incremental,
                                node_settings=self.node_settings)
        self.analysis_runner = runner
        runner.log.connect(self._append_analysis_log)
        runner.stageStarted.connect(self._analysis_stage_started)
        runner.stageSaving.connect(self._analysis_stage_saving)
        runner.stageCompleted.connect(self._analysis_stage_completed)
        runner.stageReused.connect(self._analysis_stage_reused)
        runner.stageSkipped.connect(self._analysis_stage_skipped)
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

    @Slot(int, int, str, object)
    def _analysis_stage_reused(self, position, total, title, outputs):
        self._analysis_stage_completed(position, total, title, outputs, 0)
        self._stage_position, self._stage_total, self._stage_title = position, total, title
        self._stage_started_at = perf_counter()
        self._stage_phase = "沿用結果"
        self._refresh_analysis_status()

    @Slot(int, int, str, object)
    def _analysis_stage_skipped(self, position, total, title, outputs):
        self._analysis_stage_completed(position, total, title, outputs, 0)
        self._stage_position, self._stage_total, self._stage_title = position, total, title
        self._stage_started_at = perf_counter()
        self._stage_phase = "跳過分析"
        self._refresh_analysis_status()

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
        self.run_with_dependencies_button.setEnabled(self.active_node_id is not None)
        self.run_affected_button.setEnabled(True)
        self.csv_button.setEnabled(True)
        self.parameter_scroll.setEnabled(True)
        if self.active_node_id:
            self.show_node_parameters(self.active_node_id)
        if runner.error:
            self.status_label.setText(f"分析中止：{runner.error}")
        elif runner.incremental:
            self.status_label.setText(
                f"完成：重算 {runner.completed_count} 項，沿用 {runner.reused_count} 項，"
                f"跳過 {runner.skipped_count} 項，耗時 {runner.elapsed:.2f} 秒。結果已儲存。"
            )
        else:
            self.status_label.setText(
                f"完成 {runner.completed_count}/{len(runner.rows)} 項分析，跳過 {runner.skipped_count} 項，"
                f"耗時 {runner.elapsed:.2f} 秒。結果已儲存。"
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
            QMessageBox.information(self, "尚無分析結果", f"{node_id} 尚無已儲存結果，請先執行這個分析。")
            return

        result_dir = node_dir
        dialog = ResultDialog(self)
        dialog.setWindowTitle(f"{node_id} 分析結果")
        dialog.resize(1300, 800)
        layout = QVBoxLayout(dialog)
        folder_label = QLabel(f"結果資料夾：{result_dir}")
        folder_label.setWordWrap(True)
        layout.addWidget(folder_label)

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
            save_node_settings(self.node_settings_path, self.node_settings)
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
