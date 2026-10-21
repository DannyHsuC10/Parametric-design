"""Straight-line, quasi-static braking with fixed opposed-piston calipers.

Piston counts include both sides of ONE caliper. Each axle has two identical
calipers. All lengths are metres and hydraulic pressure is Pa.
"""

from pathlib import Path

import numpy as np
import pandas as pd

G = 9.81
LINE_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "input_data" / "brake_line_data.csv"


def validate(p):
    for name, value in p.items():
        if not np.isfinite(value):
            raise ValueError(f"{name} 必須是有限數值")
        if name in {"h_cog", "brake_disc_contact_offset_m",
                    "brake_pedal_front_pressure_Pa", "brake_pedal_rear_pressure_Pa"}:
            if value < 0:
                raise ValueError(f"{name} 不可為負數")
        elif value <= 0:
            raise ValueError(f"{name} 必須大於零")
    for name in ("hl_front_weight_ratio", "brake_balance_bar_front_ratio", "brake_ideal_front_ratio"):
        if name in p and not 0 < p[name] < 1:
            raise ValueError(f"{name} 必須介於 0 與 1 之間，不含端點")
    for axle in ("front", "rear"):
        name = f"brake_caliper_{axle}_piston_count"
        if name in p and (int(p[name]) != p[name] or int(p[name]) % 2):
            raise ValueError(f"{name} 為對向固定式卡鉗兩側總活塞數，必須是正偶數")
    if "brake_safety_factor" in p and p["brake_safety_factor"] < 1:
        raise ValueError("brake_safety_factor 必須至少為 1")
    if {"brake_disc_outer_diameter_m", "brake_disc_contact_offset_m"} <= p.keys():
        if effective_disc_radius(p) <= 0:
            raise ValueError("碟盤有效半徑必須大於零：外徑 / 2 必須大於摩擦作用點偏移")


def effective_disc_radius(p):
    return p["brake_disc_outer_diameter_m"] / 2 - p["brake_disc_contact_offset_m"]


def axle_loads(p, deceleration_g):
    """Positive deceleration transfers load toward the front axle; no aero."""
    weight = p["cog_total_mass_kg"] * G
    transfer = weight * np.asarray(deceleration_g) * p["h_cog"] / p["L"]
    return (weight * p["hl_front_weight_ratio"] + transfer,
            weight * (1 - p["hl_front_weight_ratio"]) - transfer)


def design_limit_g(p):
    lift_limit = ((1 - p["hl_front_weight_ratio"]) * p["L"] / p["h_cog"]
                  if p["h_cog"] > 0 else np.inf)
    return float(min(p["mu_w"], lift_limit))


def ideal_distribution(p, deceleration_g):
    front_load, rear_load = axle_loads(p, deceleration_g)
    return front_load * deceleration_g, np.maximum(rear_load, 0) * deceleration_g


def hydraulic_geometry(p):
    result = {}
    for axle in ("front", "rear"):
        master = np.pi * (p[f"brake_master_{axle}_diameter_m"] / 2) ** 2
        # Sum of all piston areas = twice the one-side area for this caliper type.
        caliper = p[f"brake_caliper_{axle}_piston_count"] * np.pi * (
            p[f"brake_caliper_{axle}_piston_diameter_m"] / 2) ** 2
        result[axle] = (master, caliper)
    return result


def axle_force_gains(p, pedal_ratio):
    """Axle tyre force / driver pedal force, before tyre saturation."""
    geometry = hydraulic_geometry(p)
    front_share = p["brake_balance_bar_front_ratio"]
    return tuple(pedal_ratio * share / geometry[axle][0] * geometry[axle][1]
                 * p["brake_pad_mu"] * effective_disc_radius(p) * 2 / p["R_tire"]
                 for axle, share in (("front", front_share), ("rear", 1 - front_share)))


def line_pressures(p, pedal_ratio):
    """Ideal front/rear circuit pressure (Pa) at the selected driver force."""
    total_master_force = p["brake_driver_force_N"] * pedal_ratio
    front_share = p["brake_balance_bar_front_ratio"]
    return {axle: total_master_force * share / (
        np.pi * (p[f"brake_master_{axle}_diameter_m"] / 2) ** 2)
        for axle, share in (("front", front_share), ("rear", 1 - front_share))}


def first_lock_limit(p, front_gain, rear_gain):
    """First-lock pedal force for constant brake bias, before wheel lift."""
    front_static, rear_static = axle_loads(p, 0)
    transfer_per_pedal_N = (front_gain + rear_gain) * p["h_cog"] / p["L"]
    front_denominator = front_gain - p["mu_w"] * transfer_per_pedal_N
    front_limit = (p["mu_w"] * front_static / front_denominator
                   if front_denominator > 0 else np.inf)
    rear_limit = p["mu_w"] * rear_static / (rear_gain + p["mu_w"] * transfer_per_pedal_N)
    if np.isclose(front_limit, rear_limit, rtol=1e-8, atol=1e-8):
        axle = "front_and_rear"
    else:
        axle = "front" if front_limit < rear_limit else "rear"
    return float(min(front_limit, rear_limit)), axle


def fit_line_data(path=None):
    path = LINE_DATA_PATH if path is None else Path(path)
    try:
        frame = pd.read_csv(path)
    except (OSError, ValueError) as error:
        raise ValueError(f"無法讀取油管資料 {path}：{error}") from error
    columns = {"type", "pressure_MPa", "expansion_mm3_per_m"}
    if not columns <= set(frame.columns):
        raise ValueError("油管 CSV 需要 type,pressure_MPa,expansion_mm3_per_m 欄位")
    fits = {}
    for tube_type in ("Low", "High"):
        subset = frame.loc[frame["type"] == tube_type].copy()
        try:
            values = subset[["pressure_MPa", "expansion_mm3_per_m"]].to_numpy(dtype=float)
        except (ValueError, TypeError) as error:
            raise ValueError(f"{tube_type} 油管資料必須是數值") from error
        if (len(values) < 3 or not np.isfinite(values).all() or np.any(values < 0)
                or len(np.unique(values[:, 0])) < 3):
            raise ValueError(f"{tube_type} 油管需要至少三個相異壓力的非負、有限量測資料")
        subset = pd.DataFrame(values, columns=["pressure_MPa", "expansion_mm3_per_m"])
        fits[tube_type] = (subset, np.polyfit(values[:, 0], values[:, 1], 2))
    return fits
