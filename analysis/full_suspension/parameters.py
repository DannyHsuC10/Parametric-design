"""Map design results to the original full-car KC coordinates once."""

import numpy as np

from .model.KC_sys import LinearKC, SeriesKC
from .model.sus_geo.Geo_builder import create_basic_geometry
from .suspension_set.Suspension import (
    TIRE_DAMPING_NS_PER_M, BODY_TWIST_DAMPING_NMS_PER_RAD, DAMPER_TRANSITION_M_PER_S,
)


def validate(parameters):
    for name, value in parameters.items():
        if not np.isfinite(value):
            raise ValueError(f"{name} 必須為有限數值")
    positive = {
        "ms", "mu_front", "mu_rear", "Kt", "MR", "t", "hl_rear_track_m",
        "Ks_pitch_N_per_m", "Ks_roll_N_per_m", "cog_total_Ixx_kg_m2",
        "cog_total_Iyy_kg_m2", "cog_total_Izz_kg_m2",
        "hl_rear_heave_spring_ratio", "hl_rear_roll_spring_ratio",
        "tender_to_heave_stiffness_ratio",
    }
    nonnegative = {
        "h_cog", "hl_front_roll_center_m", "hl_rear_roll_center_m", "tender_bind_total_stroke_mm",
        "damped_sweep_selected_ratio_used", "full_body_twist_stiffness_Nm_per_rad",
    }
    for name in positive.intersection(parameters):
        if parameters[name] <= 0:
            raise ValueError(f"{name} 必須大於零")
    for name in nonnegative.intersection(parameters):
        if parameters[name] < 0:
            raise ValueError(f"{name} 不可為負數")
    if not 0 <= parameters.get("anti_geometry_ratio", 0.15) <= 1:
        raise ValueError("anti_geometry_ratio 必須介於 0 和 1 之間")


def apply_design_parameters(sus, p):
    """Without supplied parameters Suspension_A remains the original model.

    KCSystem.force applies MR². Rates here are mechanical KC rates; effective
    wheel rates must not be multiplied by MR² before constructing the KC.
    """
    validate(p)
    old_heave_f, old_heave_r, old_roll_f, old_roll_r = sus.shock_list[:4]
    sus.ms = p.get("ms", sus.ms)
    mu_f, mu_r = p.get("mu_front", sus.mu_list[0]), p.get("mu_rear", sus.mu_list[2])
    sus.mu_list = np.array([mu_f, mu_f, mu_r, mu_r])
    sus.m = sus.ms + float(sus.mu_list.sum())
    sus.W = sus.m * 9.81
    sus.tf, sus.tr = p.get("t", sus.tf), p.get("hl_rear_track_m", sus.tr)
    sus.h_cg = p.get("h_cog", sus.h_cg)
    position_keys = {"cog_front_axle_x_used_m", "cog_rear_axle_x_used_m", "cog_total_x_m"}
    if position_keys.intersection(p):
        if not position_keys.issubset(p):
            raise ValueError("軸距映射需要前軸、後軸與全車重心 x 座標")
        sus.lf = p["cog_front_axle_x_used_m"] - p["cog_total_x_m"]
        sus.lr = p["cog_total_x_m"] - p["cog_rear_axle_x_used_m"]
        if min(sus.lf, sus.lr) <= 0:
            raise ValueError("全車重心必須位於前、後軸之間")
        sus.l = sus.lf + sus.lr
    # Retain the original full-car convention and the LR/FR models' total inertias.
    sus.I_rate = np.array([sus.lr / sus.l, sus.lf / sus.l])
    ixx = p.get("cog_total_Ixx_kg_m2", float(sus.I[:2].sum()))
    sus.I = np.array([ixx * sus.I_rate[0], ixx * sus.I_rate[1],
                      p.get("cog_total_Iyy_kg_m2", sus.I[2]),
                      p.get("cog_total_Izz_kg_m2", sus.I[3])])
    zeta = p.get("damped_sweep_selected_ratio_used")

    # For equal wheel travel x: sum of two wheel forces = 4*k_work*MR²*x.
    # Ks_pitch is an axle rate; it must match the series pair's WORKING rate.
    front_heave_rate = p.get("Ks_pitch_N_per_m", 4 * old_heave_f.spring.stiffness(0))
    rear_heave_rate = (front_heave_rate * p["hl_rear_heave_spring_ratio"]
                       if "hl_rear_heave_spring_ratio" in p else
                       p.get("Ks_pitch_N_per_m", 4 * old_heave_r.spring.stiffness(0)))
    for index, (old, rate) in enumerate(((old_heave_f, front_heave_rate), (old_heave_r, rear_heave_rate))):
        mr = p.get("MR", old.motion_ratio.ratio(0))
        ratio = p.get("tender_to_heave_stiffness_ratio", old.spring.tender / old.spring.main)
        working_rate = rate / 4
        main_rate = working_rate * (1 + ratio) / ratio
        coefficients = {key: getattr(old.damper, key)
                        for key in ("low_comp", "high_comp", "low_reb", "high_reb")}
        if zeta is not None:
            axle_mass = sus.ms * sus.I_rate[index]
            axle_damping = 2 * zeta * np.sqrt(rate * mr**2 * axle_mass)
            coefficients = dict.fromkeys(coefficients, axle_damping / (4 * mr**2))
        sus.shock_list[index] = SeriesKC(
            main=main_rate, low=main_rate * ratio,
            # Tender reports total main+tender stroke in mm; SeriesKC uses m.
            travel=(p["tender_bind_total_stroke_mm"] / 1000.0
                    if "tender_bind_total_stroke_mm" in p else old.spring.travel),
            transition=DAMPER_TRANSITION_M_PER_S,
            mr_value=mr, travel_lim_compress=old.spring.travel_lim_compress,
            travel_lim_stretch=old.spring.travel_lim_stretch, name=old.name, **coefficients,
        )

    # Original solver: roll moment = -2*k_KC*MR²*track²*roll.
    # Heave and both roll channels use the same shared suspension MR.
    front_roll_rate = p.get("Ks_roll_N_per_m", 2 * old_roll_f.spring.k)
    rear_roll_rate = (front_roll_rate * p["hl_rear_roll_spring_ratio"]
                      if "hl_rear_roll_spring_ratio" in p else
                      p.get("Ks_roll_N_per_m", 2 * old_roll_r.spring.k))
    for index, (old, rate, track) in enumerate((
        (old_roll_f, front_roll_rate, sus.tf),
        (old_roll_r, rear_roll_rate, sus.tr),
    )):
        mr = p.get("MR", old.motion_ratio.ratio(0))
        damping = old.damper.damping(0)
        if zeta is not None:
            angular_rate = rate * mr**2 * track**2
            angular_damping = 2 * zeta * np.sqrt(angular_rate * sus.I[index])
            damping = angular_damping / (2 * mr**2 * track**2)
        sus.shock_list[index + 2] = LinearKC(k=rate / 2, c=damping, mr_value=mr, name=old.name)

    sus.body_twist = LinearKC(
        k=p.get("full_body_twist_stiffness_Nm_per_rad", sus.body_twist.spring.k),
        c=BODY_TWIST_DAMPING_NMS_PER_RAD,
        name="body_twist",
    )
    sus.tire_list = [LinearKC(k=p.get("Kt", tire.spring.k),
                              c=TIRE_DAMPING_NS_PER_M,
                              name=tire.name) for tire in sus.tire_list]
    h_front, h_rear = sus.geometry.roll_center.get_height(None)
    old_anti = sus.geometry.anti.get_rate(None)
    # MultiConstantAnti stores front rates with a minus sign internally; its
    # constructor accepts their positive magnitudes.
    old_magnitudes = (-old_anti[0], -old_anti[1], old_anti[2], old_anti[3])
    anti = [p.get("anti_geometry_ratio", value) for value in old_magnitudes]
    sus.geometry = create_basic_geometry(
        sus, h_front=p.get("hl_front_roll_center_m", h_front),
        h_rear=p.get("hl_rear_roll_center_m", h_rear),
        dive_front=anti[0], lift_front=anti[1], squat_rear=anti[2], lift_rear=anti[3],
    )


def applied_parameters(sus):
    """Record actual constructed objects rather than duplicating mapping formulas."""
    def kc(system):
        mr = float(system.motion_ratio.ratio(0))
        return {
            "spring_type": type(system.spring).__name__,
            "motion_ratio": mr,
            "working_KC_rate_N_per_m": float(system.spring.stiffness(0)),
            "wheel_working_rate_N_per_m": float(system.spring.stiffness(0) * mr**2),
            "main_KC_rate_N_per_m": float(getattr(system.spring, "main", system.spring.stiffness(0))),
            "tender_KC_rate_N_per_m": (float(system.spring.tender)
                                         if hasattr(system.spring, "tender") else None),
            "tender_to_main_ratio": (float(system.spring.tender / system.spring.main)
                                      if hasattr(system.spring, "tender") else None),
            "stiffness_switch_travel_m": (float(system.spring.travel)
                                            if hasattr(system.spring, "travel") else None),
            "low_speed_KC_damping_Ns_per_m": float(system.damper.damping(0)),
            "damper_transition_m_per_s": (float(system.damper.transition)
                                          if hasattr(system.damper, "transition") else None),
        }
    heave, roll = [kc(item) for item in sus.shock_list[:2]], [kc(item) for item in sus.shock_list[2:4]]
    return {
        "inertia_convention": "total_vehicle_matching_original_and_LR_FR_models",
        "total_mass_kg": float(sus.m), "sprung_mass_kg": float(sus.ms),
        "unsprung_mass_per_wheel_kg": sus.mu_list.tolist(),
        "front_arm_m": float(sus.lf), "rear_arm_m": float(sus.lr),
        "front_track_m": float(sus.tf), "rear_track_m": float(sus.tr),
        "cg_height_m": float(sus.h_cg),
        "roll_inertia_front_rear_kg_m2": sus.I[:2].tolist(),
        "pitch_inertia_kg_m2": float(sus.I[2]), "yaw_inertia_kg_m2": float(sus.I[3]),
        "heave_KC_front_rear": heave, "roll_KC_front_rear": roll,
        "heave_working_axle_rate_front_rear_N_per_m": [4 * x["wheel_working_rate_N_per_m"] for x in heave],
        "roll_angular_rate_front_rear_Nm_per_rad": [
            2 * x["wheel_working_rate_N_per_m"] * track**2 for x, track in zip(roll, (sus.tf, sus.tr))],
        "tire_rate_per_wheel_N_per_m": [float(x.spring.stiffness(0)) for x in sus.tire_list],
        "tire_damping_per_wheel_Ns_per_m": [float(x.damper.damping(0)) for x in sus.tire_list],
        "body_twist_damping_Nms_per_rad": float(sus.body_twist.damper.damping(0)),
        "roll_center_front_rear_m": list(sus.geometry.roll_center.get_height(None)),
        "anti_rates_front_dive_lift_rear_squat_lift": list(sus.geometry.anti.get_rate(None)),
    }
