"""Default configuration and saved vehicle sizing projects."""

import json
import math
from pathlib import Path

PROJECT_FORMAT = "VehicleInitialSizingLab"

# Numeric fields are positive by default. Bounds are inclusive unless positive is set.
GROUPS = (
    ("車輛與底盤", "車輛", (
        ("ms", "全車簧上質量", "kg"),
        ("mu", "單輪簧下質量", "kg"),
        ("h_cog", "重心高度", "m"),
        ("lf", "重心到前軸距離", "m"),
        ("lr", "重心到後軸距離", "m"),
        ("tf", "前輪距", "m"),
        ("tr", "後輪距", "m"),
        ("sprung_roll_inertia_kg_m2", "簧上側傾慣量 Ixx", "kg·m²"),
    )),
    ("性能與設計目標", "性能", (
        ("ax", "縱向加速度 ax", "g"),
        ("ay", "側向加速度 ay", "g", {"positive": False, "nonzero": True}),
        ("a_acc", "傳動加速目標", "g"),
        ("brake_ax", "煞車減速度", "g", {"hint": "留空時沿用 ax"}),
        ("target_lap_time_s", "Skidpad 目標圈時", "s", {"min": 4, "max": 6}),
        ("drive_target_speed_kmh", "目標極速", "km/h"),
        ("cg_safety_factor", "重心檢查安全係數", "", {"min": 1}),
    )),
    ("懸吊與轉向", "懸吊", (
        ("use_tender", "使用 Tender 彈簧", ""),
        ("MR", "運動比 MR", ""),
        ("zeta", "目標阻尼比 ζ", "", {"positive": False, "min": 0}),
        ("sus_travel", "懸吊壓縮行程", "m", {"max": 0.05}),
        ("target_pitch_angle_deg", "允許俯仰角", "°", {"min": 0.1, "max": 3}),
        ("target_roll_angle_deg", "允許側傾角", "°", {"min": 0.1, "max": 3}),
        ("kf", "前軸剛性權重 kf", ""),
        ("kr", "後軸剛性權重 kr", ""),
        ("N", "Tender 頻率除數 N", "", {"hint": "僅在啟用 Tender 時使用"}),
        ("min_turn_radius_m", "最小轉彎半徑", "m"),
        ("kpi_deg", "主銷內傾角 KPI", "°", {"positive": False}),
        ("rc_chassis_stiffness_ratio", "前 RC 車體／懸吊剛性比", ""),
        ("anti_front_chassis_stiffness_N_per_m", "前 Anti 車體等效剛性", "N/m"),
        ("anti_rear_chassis_stiffness_N_per_m", "後 Anti 車體等效剛性", "N/m"),
    )),
    ("輪胎與空力", "輪胎", (
        ("Kt", "單輪垂直剛性 Kt", "N/m"),
        ("wl_mu_y", "橫向摩擦係數", ""),
        ("mu_w", "縱向摩擦係數", ""),
        ("R_tire", "輪胎有效滾動半徑", "m"),
        ("A_air", "空力有效面積", "m²"),
        ("air_density_kg_per_m3", "空氣密度", "kg/m³"),
        ("F_ref_ratio", "下壓力施加比例", "", {"positive": False, "min": 0, "max": 1}),
        ("wl_aero_front_ratio", "下壓力前軸分配", "", {"positive": False, "min": 0, "max": 1}),
    )),
    ("馬達與煞車", "馬達", (
        ("drive_motor_torque_Nm", "單顆馬達最大扭矩", "N·m"),
        ("drive_motor_rpm", "馬達最高轉速", "rpm"),
        ("brake_driver_force_N", "車手煞車踏力", "N"),
    )),
)


def form_schema():
    groups = []
    for title, tab, entries in GROUPS:
        fields = []
        for name, label, unit, *options in entries:
            fields.append({
                "name": name, "label": label, "unit": unit,
                "kind": "checkbox" if name == "use_tender" else "number",
                "positive": True, **(options[0] if options else {}),
            })
        groups.append({"title": title, "tab": tab, "fields": fields})
    return groups


SCHEMA = form_schema()
FIELDS = {field["name"]: field for group in SCHEMA for field in group["fields"]}


class FieldError(ValueError):
    def __init__(self, field, message):
        self.field = field["name"]
        super().__init__(f"{field['label']}{message}")


def validate_inputs(values):
    if not isinstance(values, dict) or values.keys() - FIELDS.keys():
        raise ValueError("參數格式有誤。")

    for name, value in values.items():
        field = FIELDS[name]
        if field["kind"] == "checkbox":
            if type(value) is not bool:
                raise FieldError(field, "須為開啟或關閉。")
            continue
        if value is None and name == "brake_ax":
            continue
        if type(value) not in (int, float) or not math.isfinite(value):
            raise FieldError(field, "須填入有限數值。")
        if field["positive"] and value <= 0:
            raise FieldError(field, "須大於 0。")
        if field.get("nonzero") and value == 0:
            raise FieldError(field, "須為非零值。")
        minimum, maximum = field.get("min"), field.get("max")
        if minimum is not None and value < minimum:
            raise FieldError(field, f"須至少為 {minimum:g}。")
        if maximum is not None and value > maximum:
            raise FieldError(field, f"須小於或等於 {maximum:g}。")
    return values


def read_project(path):
    return parse_project(path.read_text(encoding="utf-8-sig"))


def parse_project(text):
    project = json.loads(text)
    if (not isinstance(project, dict) or project.get("application") != PROJECT_FORMAT
            or type(project.get("schema_version")) is not int or project["schema_version"] != 1):
        raise ValueError("請選擇 VehicleInitialSizingLab 的版本 1 專案 JSON。")
    values = project.get("parameters")
    if isinstance(values, dict):
        values.pop("caster_direction_check_deg", None)  # Legacy projects stored the direction check angle.
    if not isinstance(values, dict) or values.keys() not in (FIELDS.keys(), FIELDS.keys() - {"zeta"}):
        raise ValueError("專案的車輛參數欄位不完整或無法辨識。")
    if "zeta" not in values:
        # Version 1 projects originally stored the target ratio on the Dynamics tab.
        settings = project.get("dynamics_export", {})
        legacy_zeta = settings.get("zeta", 0.7) if isinstance(settings, dict) else 0.7
        values = {**values, "zeta": legacy_zeta}
    return validate_inputs(values)


def default_project():
    return read_project(Path(__file__).with_name("default_project.json"))
