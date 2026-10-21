"""Shared CSV inputs and the ten small analysis stages in five groups."""

DEFAULTS = {
    "hl_rear_track_m": 1.25,
    "hl_front_roll_center_m": 0.025,
    "hl_rear_roll_center_m": 0.05,
    "hl_rear_heave_spring_ratio": 0.8,
    "hl_rear_roll_spring_ratio": 0.75,
    "hl_front_roll_motion_ratio": 0.7,
    "hl_rear_roll_motion_ratio": 0.7,
    "hl_front_independent_motion_ratio": 0.48,
    "hl_rear_independent_motion_ratio": 0.48,
    "hl_front_heave_low_bump_zeta": 0.9,
    "hl_front_heave_low_rebound_zeta": 0.9,
    "hl_front_heave_high_bump_zeta": 0.35,
    "hl_front_heave_high_rebound_zeta": 0.4,
    "hl_rear_heave_low_bump_zeta": 1.0,
    "hl_rear_heave_low_rebound_zeta": 0.9,
    "hl_rear_heave_high_bump_zeta": 0.35,
    "hl_rear_heave_high_rebound_zeta": 0.4,
    "hl_front_roll_low_zeta": 1.0,
    "hl_front_roll_high_zeta": 0.5,
    "hl_rear_roll_low_zeta": 1.0,
    "hl_rear_roll_high_zeta": 0.5,
    "hl_knee_velocity_mm_s": 50.0,
    "hl_acceleration_g": 1.2,
    "hl_reference_case_g": 1.0,
}

SHARED_PARAMETERS = dict.fromkeys((
    "ms", "mu", "mu_front", "mu_rear", "MR", "Kt", "L", "t", "h_cog",
    "hl_front_weight_ratio", "hl_sprung_front_weight_ratio", "hl_sprung_roll_inertia_kg_m2",
    "ax", "ay", "Ks_pitch_N_per_m", "Ks_roll_N_per_m", *DEFAULTS,
), "float")

GROUPS = {
    "heave": "Heave 分析",
    "roll": "Roll 分析",
    "damper": "阻尼器與 Shock Dyno 分析",
    "independent": "獨立懸吊等效分析",
    "simulation": "工況與 ODE 時域模擬",
}

STAGES = {
    "hl_heave": ("heave", "Ride rate 與 Heave 自然頻率", (),
                 ("front_frequency_hz", "rear_frequency_hz")),
    "hl_heave_response": ("heave", "Heave step 與頻率響應", ("hl_heave",),
                          ("front_peak_mm", "rear_peak_mm")),
    "hl_roll": ("roll", "Roll 剛度分配與三自由度模態", (),
                ("gradient_deg_per_g", "mode_1_hz", "mode_2_hz", "mode_3_hz")),
    "hl_roll_response": ("roll", "Modal／physical／1DOF 響應比較", ("hl_roll",),
                         ("physical_low_fit_error", "physical_high_fit_error")),
    "hl_heave_damper": ("damper", "Heave 壓縮／回彈與高低速曲線", ("hl_heave_response", "hl_roll_response"),
                        ("front_force_250_mm_s_n", "rear_force_250_mm_s_n")),
    "hl_roll_damper": ("damper", "Roll physical fit／1DOF Shock Dyno", ("hl_heave_damper",),
                       ("front_physical_low_ns_per_m", "rear_physical_low_ns_per_m")),
    "hl_independent": ("independent", "單輪彈簧、阻尼與 ARB 等效", ("hl_heave_response", "hl_roll_response"),
                       ("front_spring_n_per_mm", "rear_spring_n_per_mm")),
    "hl_independent_damper": ("independent", "單輪阻尼設定與 Shock Dyno", ("hl_independent", "hl_heave_damper"),
                              ("front_force_250_mm_s_n", "rear_force_250_mm_s_n")),
    "hl_load_cases": ("simulation", "加速／煞車／過彎準靜態工況", ("hl_roll_damper", "hl_independent_damper"),
                      ("max_abs_pitch_deg", "max_abs_roll_deg")),
    "hl_ode": ("simulation", "非線性 ODE、姿態與輪胎 Fz", ("hl_load_cases",),
               ("braking_peak_abs_pitch_deg", "acceleration_peak_abs_pitch_deg", "lateral_min_tire_fz_n")),
}


def plugin_metadata(stage):
    group, title, dependencies, outputs = STAGES[stage]
    parameters = dict(SHARED_PARAMETERS)
    dependency_parameters = {
        f"{dependency}_{STAGES[dependency][3][0]}": "float"
        for dependency in dependencies
    }
    parameters.update(dependency_parameters)
    visible = {"ms", "mu"}
    if stage == "hl_heave":
        visible |= {"MR", "Kt", "hl_front_weight_ratio", "hl_rear_heave_spring_ratio"}
    elif stage == "hl_roll":
        visible |= {"t", "hl_rear_track_m", "h_cog", "hl_front_weight_ratio",
                    "hl_front_roll_center_m", "hl_rear_roll_center_m",
                    "hl_sprung_roll_inertia_kg_m2", "hl_rear_roll_spring_ratio"}
        visible |= {name for name in DEFAULTS if "roll_motion_ratio" in name}
    elif stage in {"hl_heave_response", "hl_heave_damper"}:
        visible = {name for name in DEFAULTS if "heave_" in name and "zeta" in name}
        visible.add("hl_knee_velocity_mm_s")
    elif stage in {"hl_roll_response", "hl_roll_damper"}:
        visible = {name for name in DEFAULTS if "roll_" in name and "zeta" in name}
        visible |= {"ay", "hl_reference_case_g", "hl_knee_velocity_mm_s"}
    elif group == "independent":
        visible = {name for name in DEFAULTS if "independent_motion_ratio" in name}
        visible.add("hl_knee_velocity_mm_s")
    elif group == "simulation":
        visible = {"ax", "ay", "L", "h_cog", "hl_acceleration_g", "hl_reference_case_g"}
    return {
        "PLUGIN_ID": stage, "TITLE": title, "DESCRIPTION": GROUPS[group],
        "PARAMETERS": parameters, "HIDDEN_PARAMETERS": set(parameters) - visible,
        "PARAMETER_DEFAULTS": DEFAULTS,
        "OUTPUTS": {f"{stage}_{name}": name for name in outputs},
    }
