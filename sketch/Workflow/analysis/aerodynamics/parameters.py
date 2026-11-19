"""Shared operating point and coefficient inputs for both aero-map stages."""

from pathlib import Path

import numpy as np

from .model import ModalAeroModel


DEFAULTS = {
    "aero_heave_m": -0.01,
    "aero_angle_min_deg": -3.0,
    "aero_angle_max_deg": 3.0,
    "aero_curve_points": 121,
    "aero_surface_points": 30,
    "aero_CD0": 1.8,
    "aero_Kh": -5.0, "aero_Kp": 0.2, "aero_Kr": 0.0,
    "aero_Khh": 50.0, "aero_Kpp": 30.0, "aero_Krr": 8.0,
    "aero_Kd_h": 0.0, "aero_Kd_p": 0.0, "aero_Kd_r": 0.0,
    "aero_front_balance": 0.45,
    "aero_K_balance_pitch": 0.20,
    "aero_K_balance_roll": 0.10,
}
MODEL_FIELDS = ("CD0", "Kh", "Kp", "Kr", "Khh", "Kpp", "Krr", "Kd_h", "Kd_p", "Kd_r",
                "front_balance", "K_balance_pitch", "K_balance_roll")
CURVE_OUTPUTS = {
    "aero_model_CL0": "Signed baseline CL passed to the 3D map (negative means downforce)",
    "aero_modal_baseline_downforce_N": "Downforce at specified heave and zero pitch/roll (N)",
    "aero_modal_baseline_drag_N": "Drag at specified heave and zero pitch/roll (N)",
    "aero_roll_min_downforce_N": "Minimum downforce in the pure roll sweep (N)",
    "aero_roll_max_downforce_N": "Maximum downforce in the pure roll sweep (N)",
    "aero_pitch_min_downforce_N": "Minimum downforce in the pure pitch sweep (N)",
    "aero_pitch_max_downforce_N": "Maximum downforce in the pure pitch sweep (N)",
}
SURFACE_OUTPUTS = {
    **{f"aero_3d_{name}_{stat}_{unit}": f"{name} {stat} ({unit})"
       for name, unit in (("downforce", "N"), ("drag", "N"), ("COP_x", "m"), ("COP_y", "m"),
                          ("F_FL", "N"), ("F_FR", "N"), ("F_RL", "N"), ("F_RR", "N"))
       for stat in ("min", "max", "mean")},
    "aero_3d_CL_min": "Minimum signed CL in the grid",
    "aero_3d_CL_max": "Maximum signed CL in the grid",
    "aero_3d_CD_min": "Minimum drag coefficient in the grid",
    "aero_3d_CD_max": "Maximum drag coefficient in the grid",
    "aero_3d_max_downforce_pitch_deg": "Grid pitch at maximum downforce (deg)",
    "aero_3d_max_downforce_roll_deg": "Grid roll at maximum downforce (deg)",
    "aero_3d_min_downforce_pitch_deg": "Grid pitch at minimum downforce (deg)",
    "aero_3d_min_downforce_roll_deg": "Grid roll at minimum downforce (deg)",
    **{f"aero_3d_dCOP_{axis}_d{angle}_m_per_rad": f"CoP {axis} sensitivity to {angle} (m/rad)"
       for axis in ("x", "y") for angle in ("pitch", "roll")},
}


def metadata(stage):
    surface = stage == "aero_3d"
    source_dir = Path(__file__).parent
    entry = source_dir.parent / ("aero_analysis_3d.py" if surface else "aero_roll_pitch_analysis.py")
    coefficient = "aero_model_CL0" if surface else "Cl"
    settings = {name: ("int" if name.endswith("_points") else "float") for name in DEFAULTS
                if name != ("aero_curve_points" if surface else "aero_surface_points")}
    parameters = {coefficient: "float", "v_ref": "float", "A_air": "float", "L": "float", "t": "float", **settings}
    return {
        "PLUGIN_ID": stage,
        "TITLE": "aero 3D" if surface else "aero_roll_pitch_analysis",
        "DESCRIPTION": "掃描 Roll／Pitch 下的下壓力、CoP、四輪空力分配與阻力。",
        "PARAMETERS": parameters,
        "PARAMETER_DEFAULTS": {name: DEFAULTS[name] for name in settings},
        "HIDDEN_PARAMETERS": {coefficient, "v_ref", "A_air", "L"},
        "OUTPUTS": SURFACE_OUTPUTS if surface else CURVE_OUTPUTS,
        "REQUIRES": ("aero_roll_pitch_analysis" if surface else "aero_cl_cd",),
        "INPUT_FILES": (*sorted(source_dir.glob("*.py")), entry),
    }


def make_model(parameters, *, surface=False):
    p = DEFAULTS | parameters
    for name, value in p.items():
        if not np.isfinite(value):
            raise ValueError(f"{name} 必須為有限數值")
    for name in ("A_air", "L", "t"):
        if p[name] <= 0:
            raise ValueError(f"{name} 必須大於零")
    if p["v_ref"] < 0 or p["aero_CD0"] < 0:
        raise ValueError("速度與基本阻力係數不可為負數")
    if not p["aero_angle_min_deg"] < p["aero_angle_max_deg"]:
        raise ValueError("姿態角度下限必須小於上限")
    for name in ("aero_curve_points", "aero_surface_points"):
        count = p[name]
        if int(count) != count or not 3 <= count <= 501:
            raise ValueError(f"{name} 必須為 3～501 的整數")
    angles = np.deg2rad([min(0, p["aero_angle_min_deg"]), max(0, p["aero_angle_max_deg"])])
    front = p["aero_front_balance"] + p["aero_K_balance_pitch"] * angles
    left = 0.5 + p["aero_K_balance_roll"] * angles
    if not 0 <= p["aero_front_balance"] <= 1 or np.any((front < 0) | (front > 1) | (left < 0) | (left > 1)):
        raise ValueError("掃描範圍內的前後與左右空力分配比例必須介於 0 與 1")
    if p["aero_CD0"] + p["aero_Kd_h"] * abs(p["aero_heave_m"]) + sum(
        p[name] * max(abs(angles)) for name in ("aero_Kd_p", "aero_Kd_r") if p[name] < 0
    ) < 0:
        raise ValueError("掃描範圍內的阻力係數不可為負數")
    return ModalAeroModel(area=p["A_air"], wheelbase=p["L"], track=p["t"],
                          CL0=p["aero_model_CL0"] if surface else -p["Cl"],
                          **{name: p[f"aero_{name}"] for name in MODEL_FIELDS})
