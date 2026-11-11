"""Bridge the browser worker to the shared project and solver modules."""

from base64 import b64encode
import json

from dynamics_export import build_dynamics_export
from excel_results import render_excel_results
from project import (
    FIELDS, PROJECT_FORMAT, SCHEMA, TENDER_PITCH_HINT_EN, FieldError, default_project, parse_project, validate_inputs,
)
from vehicle_initial_sizing import solve
from vehicle_initial_sizing_report import build_report, render_csv_results


GROUP_TEXT = {
    "車輛": ("Vehicle and Chassis", "Vehicle"),
    "性能": ("Performance and Design Targets", "Performance"),
    "懸吊": ("Suspension and Steering", "Suspension"),
    "輪胎": ("Tires and Aerodynamics", "Tires"),
    "馬達": ("Motors and Brakes", "Motors"),
}

FIELD_LABELS = {
    "ms": "Total Sprung Mass",
    "mu": "Unsprung Mass per Wheel",
    "h_cog": "Center of Gravity Height",
    "lf": "Center of Gravity to Front Axle",
    "lr": "Center of Gravity to Rear Axle",
    "tf": "Front Track Width",
    "tr": "Rear Track Width",
    "sprung_roll_inertia_kg_m2": "Sprung Mass Roll Inertia (Ixx)",
    "ax": "Longitudinal Acceleration (ax)",
    "ay": "Lateral Acceleration (ay)",
    "a_acc": "Target Drive Acceleration",
    "target_lap_time_s": "Target Skidpad Lap Time",
    "drive_target_speed_kmh": "Target Top Speed",
    "use_tender": "Use Tender Spring",
    "MR": "Motion Ratio (MR)",
    "zeta": "Target Damping Ratio (ζ)",
    "sus_travel": "Suspension Compression Travel",
    "target_pitch_angle_deg": "Allowable Pitch Angle",
    "target_roll_angle_deg": "Allowable Roll Angle",
    "kf": "Front Roll Stiffness Weight (kf)",
    "target_sprung_frequency_Hz": "Tender Target Sprung Natural Frequency",
    "min_turn_radius_m": "Minimum Turning Radius",
    "kpi_deg": "Kingpin Inclination (KPI)",
    "rc_chassis_stiffness_ratio": "Chassis-to-Suspension Stiffness Ratio",
    "Kt": "Tire Vertical Stiffness per Wheel (Kt)",
    "wl_mu_y": "Lateral Friction Coefficient",
    "mu_w": "Longitudinal Friction Coefficient",
    "R_tire": "Effective Tire Rolling Radius",
    "A_air": "Aerodynamic Reference Area",
    "air_density_kg_per_m3": "Air Density",
    "F_ref_ratio": "Downforce Scale Factor",
    "wl_aero_front_ratio": "Front Downforce Share",
    "drive_motor_torque_Nm": "Peak Torque per Motor",
    "drive_motor_rpm": "Maximum Motor Speed",
    "brake_driver_force_N": "Brake Pedal Force",
}

FIELD_HINTS = {
    "use_tender": TENDER_PITCH_HINT_EN,
    "kf": "Enter a value between 0 and 1. The rear weight is 1 − kf.",
    "target_sprung_frequency_Hz": "Used only when the tender spring is enabled.",
    "rc_chassis_stiffness_ratio": "Shared by the roll center and the front and rear anti calculations.",
}

VALIDATION_MESSAGES = {
    "須為開啟或關閉。": "must be on or off.",
    "須填入有限數值。": "must be a finite number.",
    "須大於 0。": "must be greater than 0.",
    "須小於 1。": "must be less than 1.",
    "須為非零值。": "must be nonzero.",
}

ERROR_MESSAGES = {
    "參數格式有誤。": "The parameter data is invalid.",
    "請選擇 VehicleInitialSizingLab 的版本 1 專案 JSON。": "Choose a version 1 Vehicle Initial Sizing Lab project JSON file.",
    "專案的車輛參數欄位不完整或無法辨識。": "The project has missing or unrecognized vehicle parameters.",
    "舊版 Tender 頻率除數 N 必須為大於 0 的有限數值。": "The legacy tender frequency divisor N must be positive and finite.",
    "目標 ride rate 必須小於輪胎剛性，才能反算彈簧剛性":
        "The target ride rate must be lower than the tire stiffness to calculate the spring rate.",
    "指定 FVSA 公式在這組公尺制參數下無法得到有限正長度":
        "These settings do not produce a positive, finite FVSA length. Check the suspension travel and track widths.",
    "此 a_acc 會造成前／後軸法向載重歸零或為負，無法使用接地加速齒比模型":
        "The target drive acceleration unloads an axle. Lower it to calculate the gear ratio.",
    "指定的煞車減速度會造成後軸離地，無法使用兩軸接地的理想煞車分配模型":
        "The requested braking deceleration lifts the rear axle. Lower longitudinal acceleration (ax) to calculate brake balance.",
}


def _english_schema():
    groups = []
    for group in SCHEMA:
        title, tab = GROUP_TEXT[group["tab"]]
        fields = []
        for field in group["fields"]:
            name = field["name"]
            translated = {**field, "label": FIELD_LABELS[name]}
            if "hint" in field:
                translated["hint"] = FIELD_HINTS[name]
            fields.append(translated)
        groups.append({**group, "title": title, "tab": tab, "fields": fields})
    return groups


def _english_error(action, error):
    if isinstance(error, FieldError):
        field = FIELDS[error.field]
        label = FIELD_LABELS[error.field]
        reason = str(error).removeprefix(field["label"])
        if reason in VALIDATION_MESSAGES:
            return f"{label} {VALIDATION_MESSAGES[reason]}"
        if "min" in field and reason == f"須至少為 {field['min']:g}。":
            return f"{label} must be at least {field['min']:g}."
        if "max" in field and reason == f"須小於或等於 {field['max']:g}。":
            return f"{label} must be at most {field['max']:g}."
        return f"Check the value for {label}."
    if isinstance(error, json.JSONDecodeError):
        return "Choose a valid JSON project file."
    return ERROR_MESSAGES.get(str(error), {
        "initialize": "Could not load the default parameters.",
        "import": "Could not import this project file.",
        "save": "Could not prepare the project download. Check the parameters and try again.",
        "solve": "Could not solve with these parameters. Check the values and try again.",
    }.get(action, "Unrecognized action."))


def handle_request(action, payload_json):
    payload = json.loads(payload_json)
    try:
        if action == "initialize":
            result = {"schema": _english_schema(), "parameters": default_project()}
        elif action == "import":
            result = parse_project(payload)
        elif action == "save":
            project = {"application": PROJECT_FORMAT, "schema_version": 1,
                       "parameters": validate_inputs(payload)}
            result = json.dumps(project, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        elif action == "solve":
            snapshot = solve(**payload["parameters"])
            dynamics = build_dynamics_export(snapshot, payload["name"])
            result = {
                "reports": {language: build_report(snapshot, language) for language in ("zh", "en")},
                "csv": render_csv_results(snapshot),
                "excel": b64encode(render_excel_results(snapshot)).decode("ascii"),
                "dynamics": json.dumps(dynamics, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            }
        else:
            raise ValueError("Unrecognized action.")
        response = {"result": result}
    except (ValueError, ArithmeticError) as error:
        response = {"error": _english_error(action, error), "field": getattr(error, "field", None)}
    return json.dumps(response, ensure_ascii=False, allow_nan=False)
