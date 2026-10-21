"""Brake plugins return gallery figures, tables and downstream parameters."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis_result import AnalysisResult
from .models import (G, axle_force_gains, axle_loads, design_limit_g,
                     effective_disc_radius, first_lock_limit, fit_line_data,
                     hydraulic_geometry, ideal_distribution, line_pressures, validate)

# Editable examples: the source scripts' data.xlsx is not part of this project.
DEFAULTS = {
    "brake_driver_force_N": 500.0,
    "brake_balance_bar_front_ratio": 0.6,
    "brake_master_front_diameter_m": 0.015875,
    "brake_master_rear_diameter_m": 0.01778,
    "brake_caliper_front_piston_diameter_m": 0.0254,
    "brake_caliper_rear_piston_diameter_m": 0.0254,
    "brake_caliper_front_piston_count": 4,
    "brake_caliper_rear_piston_count": 4,
    "brake_pad_mu": 0.4,
    "brake_disc_outer_diameter_m": 0.2,
    "brake_disc_contact_offset_m": 0.02,
    "brake_safety_factor": 1.5,
}
VEHICLE = dict.fromkeys(("cog_total_mass_kg", "L", "h_cog", "hl_front_weight_ratio", "mu_w"), "float")
HARDWARE = {name: ("int" if name.endswith("_count") else "float") for name in DEFAULTS
            if name != "brake_safety_factor"}
TITLES = {
    "brake_ratio": "Brake_ratio", "pedal_ratio": "Pedal_ratio",
    "brake_force": "Brake_force", "brake_hydraulic_pressure": "Brake_hydraulic_pressure",
}
PARAMETERS = {
    "brake_ratio": dict(VEHICLE),
    "pedal_ratio": {**VEHICLE, **HARDWARE, "R_tire": "float", "brake_ideal_front_ratio": "float",
                    "brake_safety_factor": "float"},
    "brake_force": {**VEHICLE, **HARDWARE, "R_tire": "float", "brake_pedal_ratio_required": "float"},
    "brake_hydraulic_pressure": {"brake_pedal_front_pressure_Pa": "float",
                                 "brake_pedal_rear_pressure_Pa": "float"},
}
REQUIRES = {
    "brake_ratio": ("max_load",), "pedal_ratio": ("brake_ratio",),
    "brake_force": ("pedal_ratio",), "brake_hydraulic_pressure": ("pedal_ratio",),
}
OUTPUTS = {
    "brake_ratio": ("brake_ideal_front_ratio", "brake_ideal_rear_ratio", "brake_design_deceleration_g",
                    "brake_ideal_fit_rear_over_front"),
    "pedal_ratio": ("brake_pedal_ratio_required", "brake_required_front_pressure_Pa",
                    "brake_required_rear_pressure_Pa", "brake_required_front_wheel_torque_Nm",
                    "brake_required_rear_wheel_torque_Nm", "brake_effective_disc_radius_m",
                    "brake_pedal_front_pressure_Pa", "brake_pedal_rear_pressure_Pa",
                    "brake_pedal_front_pressure_MPa", "brake_pedal_rear_pressure_MPa"),
    "brake_force": ("brake_front_pressure_Pa", "brake_rear_pressure_Pa", "brake_front_force_N",
                    "brake_rear_force_N", "brake_total_force_N", "brake_actual_front_ratio",
                    "brake_theoretical_deceleration_g", "brake_first_lock_driver_force_N",
                    "brake_first_lock_axle", "brake_first_lock_deceleration_g",
                    "brake_deceleration_before_lock_g", "brake_input_exceeds_first_lock"),
    "brake_hydraulic_pressure": ("brake_pressure_target_MPa", "brake_pressure_source_axle",
                                 "brake_line_low_expansion_mm3_per_m", "brake_line_high_expansion_mm3_per_m",
                                 "brake_line_low_target_in_range", "brake_line_high_target_in_range"),
}


def metadata(stage):
    return {
        "TITLE": TITLES[stage], "PLUGIN_ID": stage, "DESCRIPTION": "煞車分配、踏板比、煞車力與油管膨脹分析",
        "PARAMETERS": PARAMETERS[stage], "PARAMETER_DEFAULTS": DEFAULTS,
        "HIDDEN_PARAMETERS": {"cog_total_mass_kg", "brake_ideal_front_ratio", "brake_pedal_ratio_required",
                              "brake_pedal_front_pressure_Pa", "brake_pedal_rear_pressure_Pa"},
        "REQUIRES": REQUIRES[stage], "OUTPUTS": {name: name for name in OUTPUTS[stage]},
    }


def _figure(title, xlabel, ylabel, series):
    figure, axis = plt.subplots(figsize=(9, 6))
    for x, y, label, style in series:
        axis.plot(x, y, style, linewidth=2, label=label)
    axis.set(title=title, xlabel=xlabel, ylabel=ylabel)
    axis.grid(alpha=0.3)
    axis.legend()
    figure.tight_layout()
    return figure, axis


def _ratio(p):
    limit = design_limit_g(p)
    # Original ten-point through-origin fit, bounded by loss of rear contact.
    deceleration = np.linspace(min(0.1, limit / 10), limit, 10)
    front, rear = ideal_distribution(p, deceleration)
    slope = float(np.dot(front, rear) / np.dot(front, front))
    front_ratio = 1 / (1 + slope)
    line_front = np.linspace(0, front.max(), 200)
    figure, axis = _figure("Ideal Brake Force Distribution", "Front axle brake force (N)",
                          "Rear axle brake force (N)",
                          [(front, rear, "Ideal distribution", "o-"),
                           (line_front, slope * line_front, f"Fitted front bias: {front_ratio:.1%}", "--")])
    for x, y, ag in zip(front, rear, deceleration):
        axis.annotate(f"{ag:.2f} g", (x, y), xytext=(4, 5), textcoords="offset points", fontsize=8)
    front_load, rear_load = axle_loads(p, deceleration)
    outputs = {"brake_ideal_front_ratio": front_ratio, "brake_ideal_rear_ratio": 1 - front_ratio,
               "brake_design_deceleration_g": limit, "brake_ideal_fit_rear_over_front": slope}
    frame = pd.DataFrame({"deceleration_g": deceleration, "front_load_N": front_load,
                          "rear_load_N": np.maximum(rear_load, 0), "front_force_N": front,
                          "rear_force_N": rear, "ideal_front_ratio": front / (front + rear)})
    return AnalysisResult(figure, outputs, tables={"ideal_brake_distribution.csv": frame},
                          figure_titles={"plot.png": "理想前後煞車力分配與等效固定比例"})


def _pedal(p):
    limit = design_limit_g(p)
    front_force, rear_force = ideal_distribution(p, limit)
    radius = effective_disc_radius(p)
    geometry = hydraulic_geometry(p)
    pressures, torques, master_forces = {}, {}, {}
    rows = []
    for axle, force in (("front", front_force), ("rear", rear_force)):
        master_area, caliper_area = geometry[axle]
        torque = float(force * p["R_tire"] / 2)
        pressure = torque / (caliper_area * p["brake_pad_mu"] * radius)
        master_force = pressure * master_area
        pressures[axle], torques[axle], master_forces[axle] = pressure, torque, master_force
        rows.append({"axle": axle, "axle_normal_load_N": float(axle_loads(p, limit)[0 if axle == "front" else 1]),
                     "axle_brake_force_N": float(force), "wheel_torque_Nm": torque,
                     "caliper_total_piston_area_m2": caliper_area, "master_area_m2": master_area,
                     "caliper_to_master_area_ratio": caliper_area / master_area,
                     "line_pressure_Pa": pressure, "master_force_N": master_force})
    front_share = p["brake_balance_bar_front_ratio"]
    required = p["brake_safety_factor"] * max(master_forces["front"] / front_share,
                                              master_forces["rear"] / (1 - front_share)) / p["brake_driver_force_N"]
    applied_pressures = line_pressures(p, required)
    pressure_rows = []
    for row in rows:
        axle = row["axle"]
        applied = float(applied_pressures[axle])
        row.update(required_pressure_MPa=pressures[axle] / 1e6,
                   pedal_line_pressure_Pa=applied,
                   pedal_line_pressure_MPa=applied / 1e6,
                   pedal_line_pressure_bar=applied / 1e5)
        pressure_rows.append({"axle": axle, "driver_force_N": p["brake_driver_force_N"],
                              "pedal_ratio": float(required),
                              "balance_bar_force_share": front_share if axle == "front" else 1 - front_share,
                              "master_area_m2": row["master_area_m2"],
                              "applied_master_force_N": applied * row["master_area_m2"],
                              "line_pressure_Pa": applied, "line_pressure_MPa": applied / 1e6,
                              "line_pressure_bar": applied / 1e5,
                              "required_pressure_Pa": float(pressures[axle]),
                              "required_pressure_MPa": float(pressures[axle] / 1e6)})
    deceleration = np.linspace(0, limit, 200)
    front, rear = ideal_distribution(p, deceleration)
    front_torque, rear_torque = front * p["R_tire"], rear * p["R_tire"]
    total_torque = front_torque + rear_torque
    target = p["brake_ideal_front_ratio"]
    figure, _ = _figure(f"Brake Torque Requirement | required PR = {required:.2f}", "Deceleration (g)",
                       "Axle brake torque (Nm)",
                       [(deceleration, front_torque, "Ideal front", "-"),
                        (deceleration, rear_torque, "Ideal rear", "-"),
                        (deceleration, total_torque * target, f"Fitted front ({target:.1%})", "--"),
                        (deceleration, total_torque * (1 - target), f"Fitted rear ({1 - target:.1%})", "--")])
    summary = plt.figure(figsize=(12, 5))
    axis = summary.add_subplot()
    axis.axis("off")
    axis.set_title(f"Pedal Ratio Sizing | {limit:.3f} g | SF = {p['brake_safety_factor']:.2f}")
    axis.table(cellText=[[row["axle"], f"{row['wheel_torque_Nm']:.2f}",
                          f"{row['line_pressure_Pa'] / 1e6:.3f}",
                          f"{row['pedal_line_pressure_MPa']:.3f}",
                          f"{row['pedal_line_pressure_bar']:.2f}", f"{row['master_force_N']:.2f}"] for row in rows],
               colLabels=["Axle", "Required wheel\ntorque (Nm)", "Required\npressure (MPa)",
                          "Applied line\npressure (MPa)", "Applied line\npressure (bar)", "Required master\nforce (N)"],
               cellLoc="center", bbox=[0.01, 0.35, 0.98, 0.4])
    axis.text(0.5, 0.16, f"Required pedal ratio: {required:.3f} | Driver force: {p['brake_driver_force_N']:.1f} N\n"
              f"Balance-bar front force share: {front_share:.1%} | "
              f"Fitted ideal front brake bias: {p['brake_ideal_front_ratio']:.1%}", ha="center", va="center")
    summary.tight_layout()
    outputs = {"brake_pedal_ratio_required": float(required), "brake_effective_disc_radius_m": radius,
               **{f"brake_required_{axle}_pressure_Pa": float(pressures[axle]) for axle in pressures},
               **{f"brake_required_{axle}_wheel_torque_Nm": float(torques[axle]) for axle in torques},
               **{f"brake_pedal_{axle}_pressure_Pa": float(applied_pressures[axle]) for axle in pressures},
               **{f"brake_pedal_{axle}_pressure_MPa": float(applied_pressures[axle] / 1e6) for axle in pressures}}
    sweep = pd.DataFrame({"deceleration_g": deceleration, "ideal_front_axle_torque_Nm": front_torque,
                          "ideal_rear_axle_torque_Nm": rear_torque,
                          "target_front_axle_torque_Nm": total_torque * target,
                          "target_rear_axle_torque_Nm": total_torque * (1 - target)})
    return AnalysisResult(figure, outputs, figures={"pedal_sizing.png": summary},
                          tables={"pedal_sizing.csv": pd.DataFrame(rows), "brake_torque_requirement.csv": sweep,
                                  "pedal_line_pressure.csv": pd.DataFrame(pressure_rows)},
                          figure_titles={"plot.png": "理想與回歸固定比例的前後軸煞車扭矩", "pedal_sizing.png": "踏板比、前後油路壓力與扭矩需求"})


def _force(p):
    pedal_ratio = p["brake_pedal_ratio_required"]
    kf, kr = axle_force_gains(p, pedal_ratio)
    driver = p["brake_driver_force_N"]
    lock_force, lock_axle = first_lock_limit(p, kf, kr)
    lock_g = (kf + kr) * lock_force / p["cog_total_mass_kg"] / G
    force_grid = np.unique(np.r_[np.linspace(0, max(1000, driver, lock_force * 1.1), 101), driver, lock_force])
    front, rear = force_grid * kf, force_grid * kr
    total = front + rear
    theory_g = total / p["cog_total_mass_kg"] / G
    limited_g = np.minimum(theory_g, lock_g)
    figure, axis = _figure("Brake Force vs Driver Pedal Force", "Driver pedal force (N)", "Axle brake force (N)",
                          [(force_grid, front, "Front hydraulic demand", "-"),
                           (force_grid, rear, "Rear hydraulic demand", "-"),
                           (force_grid, total, "Total hydraulic demand", "--")])
    axis.axvline(lock_force, color="crimson", linestyle=":", label=f"First lock: {lock_axle}")
    axis.axvline(driver, color="grey", linestyle="--", label="Selected driver force")
    axis.legend()
    acceleration, axis = _figure("Deceleration vs Driver Pedal Force", "Driver pedal force (N)", "Deceleration (g)",
                                [(force_grid, theory_g, "Hydraulic demand / mass", "--"),
                                 (force_grid, limited_g, "Capped at first-lock boundary", "-")])
    axis.axhline(p["mu_w"], color="grey", linestyle=":", label="Ideal tyre friction limit")
    axis.axvline(lock_force, color="crimson", linestyle=":", label=f"First lock at {lock_g:.3f} g")
    axis.legend()
    applied_pressures = line_pressures(p, pedal_ratio)
    outputs = {"brake_front_pressure_Pa": applied_pressures["front"],
               "brake_rear_pressure_Pa": applied_pressures["rear"],
               "brake_front_force_N": driver * kf, "brake_rear_force_N": driver * kr,
               "brake_total_force_N": driver * (kf + kr), "brake_actual_front_ratio": kf / (kf + kr),
               "brake_theoretical_deceleration_g": driver * (kf + kr) / p["cog_total_mass_kg"] / G,
               "brake_first_lock_driver_force_N": lock_force, "brake_first_lock_axle": lock_axle,
               "brake_first_lock_deceleration_g": float(lock_g),
               "brake_deceleration_before_lock_g": float(min(driver, lock_force) * (kf + kr) / p["cog_total_mass_kg"] / G),
               "brake_input_exceeds_first_lock": bool(driver > lock_force)}
    outputs = {name: float(value) if isinstance(value, np.floating) else value for name, value in outputs.items()}
    frame = pd.DataFrame({"driver_force_N": force_grid, "front_force_N": front, "rear_force_N": rear,
                          "total_force_N": total, "hydraulic_demand_deceleration_g": theory_g,
                          "deceleration_capped_at_first_lock_g": limited_g,
                          "beyond_first_lock": force_grid > lock_force})
    return AnalysisResult(figure, outputs, figures={"deceleration_vs_force.png": acceleration},
                          tables={"brake_force_sweep.csv": frame,
                                  "selected_brake_force.csv": pd.DataFrame([outputs])},
                          figure_titles={"plot.png": "踏力與前後軸理論煞車力", "deceleration_vs_force.png": "理論減速度與首次鎖死界限"})


def _hydraulic(p):
    front_pressure = p["brake_pedal_front_pressure_Pa"]
    rear_pressure = p["brake_pedal_rear_pressure_Pa"]
    target = max(front_pressure, rear_pressure) / 1e6
    source = ("front" if front_pressure > rear_pressure else
              "rear" if rear_pressure > front_pressure else "front_and_rear")
    fits = fit_line_data()
    figures, titles, tables, outputs, rows = {}, {}, {}, {}, []
    outputs.update(brake_pressure_target_MPa=float(target), brake_pressure_source_axle=source)
    for tube_type, (data, coefficients) in fits.items():
        key = tube_type.lower()
        pressure = np.linspace(0, max(20, target, data["pressure_MPa"].max()), 201)
        expansion = np.polyval(coefficients, pressure)
        target_expansion = float(np.polyval(coefficients, target))
        in_range = bool(data["pressure_MPa"].min() <= target <= data["pressure_MPa"].max())
        figure, axis = _figure(f"{tube_type} Expansion Tube", "Pressure (MPa)", "Volume expansion per length (mm³/m)",
                              [(pressure, expansion, "Quadratic fit (outside measured range: extrapolation)", "-")])
        axis.scatter(data["pressure_MPa"], data["expansion_mm3_per_m"], label="Source data", zorder=3)
        axis.scatter([target], [target_expansion], label=f"Max circuit ({source}): {target:.2f} MPa", marker="x", s=80, zorder=4)
        axis.axvspan(data["pressure_MPa"].min(), data["pressure_MPa"].max(), alpha=0.08, label="Measured pressure range")
        axis.legend(fontsize=8)
        filename = "plot.png" if tube_type == "Low" else "high_expansion_tube.png"
        figures[filename] = figure
        titles[filename] = f"{tube_type} 油管膨脹與前後回路最高壓力"
        tables[f"{key}_expansion_curve.csv"] = pd.DataFrame({"pressure_MPa": pressure, "expansion_mm3_per_m": expansion})
        rows.append({"type": tube_type, "target_pressure_MPa": target,
                     "front_line_pressure_MPa": front_pressure / 1e6,
                     "rear_line_pressure_MPa": rear_pressure / 1e6,
                     "selected_pressure_source": source,
                     "target_expansion_mm3_per_m": target_expansion, "target_in_measured_range": in_range,
                     "quadratic_coefficient": coefficients[0], "linear_coefficient": coefficients[1],
                     "constant_coefficient": coefficients[2]})
        outputs[f"brake_line_{key}_expansion_mm3_per_m"] = target_expansion
        outputs[f"brake_line_{key}_target_in_range"] = in_range
        if not in_range:
            print(f"{tube_type} 油管：目標壓力 {target:g} MPa 位於量測範圍之外，結果為二次曲線外插。")
    tables["brake_line_target.csv"] = pd.DataFrame(rows)
    tables["brake_line_source.csv"] = pd.concat([data.assign(type=name) for name, (data, _) in fits.items()], ignore_index=True)
    return AnalysisResult(figures.pop("plot.png"), outputs, figures=figures, tables=tables, figure_titles=titles)


def run(stage, parameters):
    p = DEFAULTS | parameters
    # Validate just this stage's inputs, without unrelated brake settings.
    validate({name: p[name] for name in PARAMETERS[stage]})
    result = {"brake_ratio": _ratio, "pedal_ratio": _pedal, "brake_force": _force,
              "brake_hydraulic_pressure": _hydraulic}[stage](p)
    for name, value in result.outputs.items():
        print(f"{name}: {value}")
    result.artifacts["analysis.md"] = Path(__file__).with_name("README.md").read_text(encoding="utf-8")
    return result
