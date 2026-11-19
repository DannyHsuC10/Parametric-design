"""Model catalog and conversion from shared vehicle values to the original models."""

from pathlib import Path

import numpy as np

from .batch_cases import FAMILIES, compatibility_error

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = Path(__file__).resolve().parent
SOURCE_ANALYSIS = "damped_oscillation_analysis"
QUARTER_STIFFNESS = "Ks_required_target_frequency_N_per_m"

# Diagram arrows describe model progression; each model can run independently
# after the physical parameter sources have been computed.
STAGES = {
    "single_spring_model": ("quarter", "single", "single_spring_model"),
    "one_eighth_suspension_model": ("quarter", "one_eighth", "one_eighth_suspension_model"),
    "double_spring_model": ("quarter", "double", "Double_spring_model"),
    "quarter_suspension_model": ("quarter", "quarter", "Quarter_suspension_model"),
    "two_mass_suspension_2dof_model": ("LR", "2mass_2dof", "two_mass_suspension_2DOF_model"),
    "two_mass_suspension_model": ("LR", "2mass", "two_mass_suspension_model"),
    "half_suspension_2dof_model_lr": ("LR", "half_2dof", "Half_suspension_2DOF_model（LR 左右）"),
    "half_suspension_model_lr": ("LR", "half", "Half_suspension_model（LR 左右）"),
    "half_rollcenter_all_model": ("LR", "rollcenter_all", "Half_rollcenter_all_model"),
    "half_suspension_2dof_model_fr": ("FR", "half_2dof", "Half_suspension_2DOF_model（FR 前後）"),
    "half_suspension_model_fr": ("FR", "half", "Half_suspension_model（FR 前後）"),
}

SCENARIO_TITLES = {
    "step": "階躍 step", "bump": "凸起 bump", "sine": "正弦 sine", "random": "隨機路面 random",
    "bump_left": "左輪凸起 bump_left", "bump_both": "雙輪凸起 bump_both",
    "sine_left": "左輪正弦 sine_left", "cornering": "過彎 cornering",
    "impulse_drive": "前後輪路面脈衝 impulse_drive", "accelerate": "加速 accelerate",
}


def scenarios_for(stage):
    family, model, _ = STAGES[stage]
    return [name for name in FAMILIES[family].scenarios
            if compatibility_error(family, model, name) is None]


def plugin_metadata(stage):
    family, _, title = STAGES[stage]
    stiffness_names = ([QUARTER_STIFFNESS] if family == "quarter" else
                       ["Ks", "Ks_pitch_N_per_m", "Ks_roll_N_per_m"])
    names = ["ms", "mu", *stiffness_names, "Kt", "MR",
             "hl_rear_heave_spring_ratio", "damped_sweep_selected_ratio_used",
             "damped_sweep_selected_coefficient_Ns_per_m"]
    if family == "LR":
        names += ["t", "h_cog", "cog_total_Ixx_kg_m2",
                  "k_frame_to_roll_ratio"]
        if stage in {"half_suspension_model_lr", "half_rollcenter_all_model"}:
            names += ["hl_front_roll_center_m", "hl_rear_roll_center_m"]
        visible = {"t", "Kt", "k_frame_to_roll_ratio"}
        if stage == "half_rollcenter_all_model":
            names += ["zeta_frame"]
            visible.add("zeta_frame")
    elif family == "FR":
        names += ["L", "h_cog", "cog_total_Iyy_kg_m2", "anti_geometry_ratio"]
        visible = {"Kt", "hl_rear_heave_spring_ratio"}
    else:
        visible = {"Kt", "MR"}
    outputs = {f"{stage}_case_count": "相容工況數"}
    for scenario in scenarios_for(stage):
        for metric, label in (("peak_body_m", "車身最大絕對位移 (m)"),
                              ("peak_acceleration_m_s2", "車身最大絕對加速度 (m/s²)"),
                              ("peak_tire_force_N", "模型輪胎力最大絕對值 (N)")):
            outputs[f"{stage}_{scenario}_{metric}"] = f"{scenario}｜{label}"
    # Include the bundle, renderer, and adapter sources in incremental invalidation.
    files = sorted(path for path in SOURCE_DIR.rglob("*.py")
                   if "__pycache__" not in path.parts)
    suspension = FAMILIES[family].suspension_factory()
    default_sources = {"t": "track", "L": "l", "Kt": "kt"}
    defaults = {
        name: getattr(suspension, default_sources.get(name, name))
        for name in visible if hasattr(suspension, default_sources.get(name, name))
    }
    defaults["MR"] = float(np.sqrt(suspension.kw / suspension.ks)) if family == "quarter" else 1.0
    if family == "LR":
        defaults["k_frame_to_roll_ratio"] = suspension.k_frame / suspension.k_roll
    if family == "FR":
        defaults["hl_rear_heave_spring_ratio"] = 0.8
    requires = (SOURCE_ANALYSIS,)
    if stage in {"half_suspension_model_lr", "half_rollcenter_all_model"}:
        requires += ("roll_center_same_load_r",)
    return {
        "PLUGIN_ID": stage, "TITLE": title,
        "DESCRIPTION": "執行此模型的所有相容工況；案例設定在 analysis/suspension_models/batch_cases.py。",
        "PARAMETERS": dict.fromkeys(names, "float"), "HIDDEN_PARAMETERS": set(names) - visible,
        "VISIBLE_PARAMETERS": visible, "PARAMETER_DEFAULTS": defaults,
        "OUTPUTS": outputs, "REQUIRES": requires, "INPUT_FILES": tuple(files),
    }


def make_suspension(family, parameters):
    """Keep Suspension.py defaults for values without an upstream counterpart.

    ms is the whole vehicle's sprung mass; these models store a quarter at each
    corner. Each half-car uses half the corresponding whole-vehicle inertia.
    """
    suspension = FAMILIES[family].suspension_factory()
    if not parameters:
        return suspension
    for name, value in parameters.items():
        if not np.isfinite(value):
            raise ValueError(f"{name} 必須為有限數值")
        if name in {"ms", "mu", "Ks", QUARTER_STIFFNESS, "Ks_pitch_N_per_m", "Ks_roll_N_per_m", "Kt", "MR", "t", "L",
                    "hl_sprung_roll_inertia_kg_m2", "cog_total_Ixx_kg_m2", "cog_total_Iyy_kg_m2",
                    "k_frame_to_roll_ratio", "m_frame", "Iy",
                    "hl_rear_heave_spring_ratio"} and value <= 0:
            raise ValueError(f"{name} 必須大於零")
        if name in {"damped_sweep_selected_ratio_used", "damped_sweep_selected_coefficient_Ns_per_m", "h_cog",
                    "ct", "zeta_frame", "k_left", "k_right", "k_front", "k_rear"} and value < 0:
            raise ValueError(f"{name} 不可為負數")

    old_ms, old_mu = suspension.ms, suspension.mu
    suspension.ms = parameters.get("ms", old_ms * 4) / 4
    suspension.mu = parameters.get("mu", old_mu)
    suspension.m_corner = suspension.ms + suspension.mu
    suspension.kt = parameters.get("Kt", suspension.kt)
    if family == "quarter":
        old_ks, old_cs = suspension.ks, suspension.cs
        motion_ratio = parameters.get("MR", np.sqrt(suspension.kw / old_ks))
        suspension.ks = parameters.get(QUARTER_STIFFNESS, old_ks)
        if "damped_sweep_selected_coefficient_Ns_per_m" in parameters:
            suspension.cs = parameters["damped_sweep_selected_coefficient_Ns_per_m"]
        elif "damped_sweep_selected_ratio_used" in parameters:
            suspension.cs = 2 * parameters["damped_sweep_selected_ratio_used"] * np.sqrt(suspension.ks * suspension.ms)
        else:
            # Preserve the original quarter constructor's unsprung-mass reference.
            suspension.cs = old_cs * np.sqrt(suspension.ks * suspension.mu / (old_ks * old_mu))
        suspension.kw = suspension.ks * motion_ratio**2
        suspension.cw = suspension.cs * motion_ratio**2
        suspension.ride_rate = suspension.kw * suspension.kt / (suspension.kw + suspension.kt)
        return suspension

    suspension.zeta = parameters.get("damped_sweep_selected_ratio_used", suspension.zeta)
    suspension.h_cg = parameters.get("h_cog", suspension.h_cg)
    # Half-car configurations represent half of the whole-car stiffness. The
    # Ks_pitch/Ks_roll values are already spring rates (Tire_Stiffness has
    # applied MR), so each half-car rate is simply the corresponding value / 2.
    if family == "LR":
        suspension.track = parameters.get("t", suspension.track)
        suspension.Ix = parameters.get("cog_total_Ixx_kg_m2", suspension.Ix * 2) / 2
        front_roll_center = parameters.get("hl_front_roll_center_m")
        rear_roll_center = parameters.get("hl_rear_roll_center_m")
        if front_roll_center is not None and rear_roll_center is not None:
            suspension.h_rc = (front_roll_center + rear_roll_center) / 2
        # Match the RC study's m_axle/4 using this model's half-car sprung mass.
        suspension.m_frame = (2 * suspension.ms) / 4
        suspension.k_left = 0.0
        suspension.k_right = 0.0
        old_roll = suspension.k_roll
        pitch_rate = parameters.get("Ks_pitch_N_per_m", parameters.get("Ks"))
        roll_rate = parameters.get("Ks_roll_N_per_m", parameters.get("Ks"))
        if pitch_rate is not None:
            suspension.k_heave = pitch_rate / 2
        if roll_rate is not None:
            suspension.k_roll = roll_rate / 2
            scale = suspension.k_roll / old_roll
            suspension.k_frame *= scale
        suspension.k_frame = suspension.k_roll * parameters.get(
            "k_frame_to_roll_ratio", suspension.k_frame / suspension.k_roll
        )
        suspension.zeta_frame = parameters.get("zeta_frame", suspension.zeta_frame)
        suspension.c_frame = 2 * suspension.zeta_frame * np.sqrt(suspension.k_frame * suspension.m_frame)
        suspension.c_heave = 2 * suspension.zeta * np.sqrt(suspension.k_heave * suspension.ms)
        suspension.c_roll = 2 * suspension.zeta * np.sqrt(suspension.k_roll * 2 * suspension.Ix / suspension.track**2)
        effective = 1 / (1 / (2 * suspension.ms) + (suspension.track / 2)**2 / suspension.Ix)
        for side in ("left", "right"):
            setattr(suspension, f"c_{side}", 2 * suspension.zeta * np.sqrt(getattr(suspension, f"k_{side}") * effective))
    else:
        # Preserve the original front/rear arm ratio when applying the wheelbase.
        scale = parameters.get("L", suspension.l) / suspension.l
        suspension.lf *= scale
        suspension.lr *= scale
        suspension.l = suspension.lf + suspension.lr
        suspension.Iy = parameters.get("cog_total_Iyy_kg_m2", suspension.Iy * 2) / 2
        anti_ratio = parameters.get("anti_geometry_ratio")
        if anti_ratio is not None:
            if not 0 <= anti_ratio <= 1:
                raise ValueError("anti_geometry_ratio 必須介於 0 和 1 之間")
            suspension.anti_dive_front = anti_ratio
            suspension.anti_squat_rear = anti_ratio
        suspension.k_front = 0.0
        suspension.k_rear = 0.0
        pitch_rate = parameters.get("Ks_pitch_N_per_m", parameters.get("Ks"))
        if pitch_rate is not None:
            suspension.k_heave_f = pitch_rate / 2
        rear_ratio = parameters.get("hl_rear_heave_spring_ratio")
        if rear_ratio is not None:
            suspension.k_heave_r = suspension.k_heave_f * rear_ratio
        elif pitch_rate is not None:
            suspension.k_heave_r = suspension.k_heave_f
        for side, suffix, arm in (("front", "f", suspension.lf), ("rear", "r", suspension.lr)):
            effective = 1 / (1 / (2 * suspension.ms) + arm**2 / suspension.Iy)
            setattr(suspension, f"c_heave_{suffix}", 2 * suspension.zeta * np.sqrt(getattr(suspension, f"k_heave_{suffix}") * effective))
            setattr(suspension, f"c_{side}", 2 * suspension.zeta * np.sqrt(getattr(suspension, f"k_{side}") * effective))
    return suspension
