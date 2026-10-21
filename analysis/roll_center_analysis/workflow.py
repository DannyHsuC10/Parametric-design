"""Integrate the three original roll-center studies with the shared CSV flow."""

from dataclasses import asdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis_result import AnalysisResult
from .models import G, make_axle, response, sweep, time_grid, validate

DEFAULTS = {
    "rc_chassis_stiffness_ratio": 10.0,
}
SCAN_SETTINGS = {
    "rc_sweep_min_ratio": 0.01,
    "rc_sweep_max_ratio": 0.99,
    "rc_sweep_points": 50,
    "rc_time_step_s": 0.001,
    "rc_simulation_duration_s": 2.0,
}
COMMON = dict.fromkeys(("ms", "h_cog", "hl_sprung_front_weight_ratio", "cog_total_Ixx_kg_m2",
                       "Ks_roll_N_per_m", "t", "hl_front_roll_motion_ratio", "ay"), "float")
PARAMETERS = {
    "roll_center": {"rc_chassis_stiffness_ratio": "float"},
    "roll_center_min_load_f": COMMON,
    "roll_center_same_load_r": {**COMMON, "hl_rear_track_m": "float",
                               "hl_rear_roll_spring_ratio": "float", "hl_rear_roll_motion_ratio": "float",
                               "rc_front_optimal_height_m": "float",
                               "rc_front_min_peak_rate_N_per_s": "float"},
}
REQUIRES = {"roll_center": ("overall_rigidity",), "roll_center_min_load_f": ("roll_center",),
            "roll_center_same_load_r": ("roll_center_min_load_f",)}
OUTPUTS = {
    "roll_center": ("rc_normalized_optimal_ratio", "rc_normalized_min_stiffness",
                    "rc_normalized_grid_optimal_ratio"),
    "roll_center_min_load_f": ("rc_front_optimal_ratio", "rc_front_optimal_height_m",
                               "rc_front_min_peak_rate_N_per_s",
                               "rc_front_optimal_peak_time_s", "rc_front_objective_active",
                               "hl_front_roll_center_m"),
    "roll_center_same_load_r": ("rc_rear_matched_ratio", "rc_rear_matched_height_m",
                                "rc_rear_matched_peak_rate_N_per_s", "rc_rear_match_error_N_per_s",
                                "rc_rear_objective_active",
                                "hl_rear_roll_center_m"),
}


def metadata(stage):
    return {"PLUGIN_ID": stage, "TITLE": stage, "DESCRIPTION": "Roll Center 剛性與首次載重轉移率分析",
            "PARAMETERS": PARAMETERS[stage], "PARAMETER_DEFAULTS": DEFAULTS,
            "HIDDEN_PARAMETERS": {"ms", "hl_sprung_front_weight_ratio", "cog_total_Ixx_kg_m2",
                                  "Ks_roll_N_per_m", "rc_front_optimal_height_m", "rc_front_min_peak_rate_N_per_s"},
            "REQUIRES": REQUIRES[stage], "OUTPUTS": {name: name for name in OUTPUTS[stage]}}


def _curve(title, xlabel, ylabel):
    figure, axis = plt.subplots(figsize=(9, 5.5))
    axis.set(title=title, xlabel=xlabel, ylabel=ylabel)
    axis.grid(alpha=0.3)
    return figure, axis


def _frame(result):
    return pd.DataFrame({name: values for name, values in result.items() if isinstance(values, np.ndarray)})


def _pulse_plot(axle, optimum, title):
    figure, axis = _curve(title, "Time (s)", "First-pulse transfer rate (N/s)")
    times = optimum["time_s"]
    for name, label in (("suspension_first_pulse_rate_N_per_s", "Optimized suspension"),
                        ("chassis_first_pulse_rate_N_per_s", "Optimized chassis"),
                        ("total_first_pulse_rate_N_per_s", "Optimized total")):
        axis.plot(times, optimum[name], label=label, linewidth=1.8)
    axis.scatter(optimum["peak_time_s"], optimum["peak_rate_N_per_s"], color="crimson", zorder=4)
    axis.set_xlim(0, 1.08 * max(np.pi / axle.roll_frequency, np.pi / axle.chassis_frequency))
    axis.legend(fontsize=9)
    figure.tight_layout()
    return figure


def _normalized(p):
    ratio = np.linspace(0, 1, 300)
    chassis = p["rc_chassis_stiffness_ratio"]
    stiffness = (1 - ratio)**2 + chassis * ratio**2
    index = int(np.argmin(stiffness))
    optimum = 1 / (1 + chassis)
    minimum = chassis / (1 + chassis)
    figure, axis = _curve("Equivalent Roll Stiffness vs Roll Center Height", "Roll center height / CG height",
                         "Equivalent stiffness / suspension stiffness")
    axis.plot(ratio, stiffness, linewidth=2, label=f"Chassis / suspension = {chassis:g}")
    axis.scatter(optimum, minimum, color="crimson", zorder=4, label=f"Minimum: RC/CG = {optimum:.4f}")
    axis.legend()
    figure.tight_layout()
    return AnalysisResult(figure, {"rc_normalized_optimal_ratio": float(optimum),
                                  "rc_normalized_min_stiffness": float(minimum),
                                  "rc_normalized_grid_optimal_ratio": float(ratio[index])},
                          tables={"roll_center_stiffness.csv": pd.DataFrame({"rc_height_ratio": ratio,
                                                                            "normalized_stiffness": stiffness})},
                          figure_titles={"plot.png": "Roll Center 高度與正規化等效剛性"})


def _front(p):
    axle = make_axle(p)
    times = time_grid(p, axle)
    ratios = np.linspace(p["rc_sweep_min_ratio"], p["rc_sweep_max_ratio"], p["rc_sweep_points"])
    acceleration = -p["ay"] * G
    peaks = sweep(axle, ratios, acceleration, times)
    index = int(np.argmin(peaks))
    height = float(ratios[index] * p["h_cog"])
    optimum = response(axle, height, acceleration, times)
    figure, axis = _curve("Front RC Height vs Peak Load Transfer Rate", "Front roll center height (% CG)",
                         "Peak first-pulse transfer rate (N/s)")
    axis.plot(ratios * 100, peaks, "o-", markersize=4, label="Front RC sweep")
    axis.scatter(ratios[index] * 100, peaks[index], color="crimson", zorder=4,
                 label=f"Minimum: {ratios[index]:.1%} CG = {height:.4f} m")
    axis.legend(fontsize=9)
    figure.tight_layout()
    outputs = {"rc_front_optimal_ratio": float(ratios[index]), "rc_front_optimal_height_m": height,
               "rc_front_min_peak_rate_N_per_s": float(peaks[index]),
               "rc_front_optimal_peak_time_s": optimum["peak_time_s"], "rc_front_objective_active": bool(p["ay"] > 0),
               "hl_front_roll_center_m": height}
    return AnalysisResult(figure, outputs,
                          figures={"front_load_transfer_pulse.png": _pulse_plot(axle, optimum, "Front First Load Transfer Pulses")},
                          tables={"front_roll_center_sweep.csv": pd.DataFrame({"rc_height_ratio": ratios,
                                     "rc_height_m": ratios * p["h_cog"], "peak_rate_N_per_s": peaks}),
                                  "front_optimal_response.csv": _frame(optimum),
                                  "axle_model.csv": pd.DataFrame([asdict(axle)])},
                          figure_titles={"plot.png": "前軸 RC 高度與最低載重轉移率峰值",
                                         "front_load_transfer_pulse.png": "前軸懸吊、車架與總轉移率首次脈衝"})


def _rear(p):
    front, rear = make_axle(p), make_axle(p, rear=True)
    # Match the exact upstream front sampling basis; add rear characteristic times
    # only for rear evaluation so the comparison target is not silently changed.
    front_times, rear_times = time_grid(p, front), time_grid(p, rear)
    acceleration = -p["ay"] * G
    ratios = np.linspace(p["rc_sweep_min_ratio"], p["rc_sweep_max_ratio"], p["rc_sweep_points"])
    peaks = sweep(rear, ratios, acceleration, rear_times)
    target = p["rc_front_min_peak_rate_N_per_s"]
    errors = np.abs(peaks - target)
    index = int(np.argmin(errors))
    height = float(ratios[index] * p["h_cog"])
    front_result = response(front, p["rc_front_optimal_height_m"], acceleration, front_times)
    rear_result = response(rear, height, acceleration, rear_times)
    figure, axis = _curve("Rear RC Matching Front Transient Load Transfer", "Rear roll center height (% CG)",
                         "Peak first-pulse transfer rate (N/s)")
    axis.plot(ratios * 100, peaks, linewidth=2, label="Rear RC sweep")
    axis.axhline(target, linestyle="--", label="Optimized front peak from previous node")
    axis.scatter(ratios[index] * 100, peaks[index], color="crimson", zorder=4,
                 label=f"Best match: {ratios[index]:.1%} CG = {height:.4f} m")
    axis.legend(fontsize=9)
    figure.tight_layout()
    pulse, axis = _curve("Matched Front / Rear First Load Transfer Pulses", "Time (s)", "First-pulse transfer rate (N/s)")
    axis.plot(front_times, front_result["total_first_pulse_rate_N_per_s"], label="Optimized front", linewidth=2)
    axis.plot(rear_times, rear_result["total_first_pulse_rate_N_per_s"], "--", label="Matched rear", linewidth=2)
    axis.set_xlim(0, 1.08 * max(np.pi / frequency for axle in (front, rear)
                              for frequency in (axle.roll_frequency, axle.chassis_frequency)))
    axis.legend()
    pulse.tight_layout()
    outputs = {"rc_rear_matched_ratio": float(ratios[index]), "rc_rear_matched_height_m": height,
               "rc_rear_matched_peak_rate_N_per_s": float(peaks[index]), "rc_rear_match_error_N_per_s": float(errors[index]),
               "rc_rear_objective_active": bool(p["ay"] > 0),
               "hl_rear_roll_center_m": height}
    return AnalysisResult(figure, outputs, figures={"matched_load_transfer_pulse.png": pulse},
                          tables={"rear_roll_center_sweep.csv": pd.DataFrame({"rc_height_ratio": ratios,
                                     "rc_height_m": ratios * p["h_cog"], "peak_rate_N_per_s": peaks,
                                     "front_target_peak_rate_N_per_s": target, "absolute_error_N_per_s": errors}),
                                  "rear_matched_response.csv": _frame(rear_result),
                                  "front_reference_response.csv": _frame(front_result),
                                  "axle_models.csv": pd.DataFrame([{"axle": "front", **asdict(front)}, {"axle": "rear", **asdict(rear)}])},
                          figure_titles={"plot.png": "後軸 RC 搜尋與前軸最佳峰值匹配",
                                         "matched_load_transfer_pulse.png": "前軸最佳與後軸匹配的首次轉移率脈衝"})


def run(stage, parameters):
    p = DEFAULTS | SCAN_SETTINGS | parameters
    validate(p)
    result = {"roll_center": _normalized, "roll_center_min_load_f": _front, "roll_center_same_load_r": _rear}[stage](p)
    result.artifacts["analysis.md"] = (Path(__file__).with_name("notes") / f"{stage}.md").read_text(encoding="utf-8")
    for name, value in result.outputs.items():
        print(f"{name}: {value}")
    return result
