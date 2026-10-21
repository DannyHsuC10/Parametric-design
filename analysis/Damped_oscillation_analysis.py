"""Quarter-car damping-ratio sweep and dynamic tire-load variation."""

import matplotlib.pyplot as plt
import numpy as np

from damping_models import QUARTER_CAR_PARAMETERS, quarter_car_response, system_settings

TITLE = "Damped_oscillation_analysis"
PLUGIN_ID = "damped_oscillation_analysis"
DESCRIPTION = "Sweep quarter-car damping ratio and compare sprung displacement and tire-load variation."
PARAMETERS = dict(QUARTER_CAR_PARAMETERS)
HIDDEN_PARAMETERS = {"Ks", "damping_rate_best_ratio"}

DAMPING_RATIOS = (0.0, 0.2, 0.4, 0.7, 1.0)
INITIAL_STATE = (0.05, 0.0, 0.0, 0.0)
SIMULATION_TIME_S = 3.0
OUTPUT_SAMPLES = 1000
GRAVITY_M_PER_S2 = 9.81
RK45_RTOL = 0.001
RK45_ATOL = 0.000001


def ratio_key(ratio):
    return f"{ratio:.1f}".replace(".", "p")


OUTPUTS = {
    "damped_sweep_stiffness_used_N_per_m": "Suspension spring stiffness Ks (N/m)",
    "damped_sweep_critical_coefficient_Ns_per_m": "Sprung-mass reference critical damping (N s/m)",
    "damped_sweep_static_tire_load_N": "Static tire load (N)",
    "damped_sweep_selected_ratio_used": "Selected damping ratio supplied by damping_rate",
    "damped_sweep_selected_coefficient_Ns_per_m": "Damping coefficient at the selected ratio (N s/m)",
    "damped_sweep_selected_peak_abs_sprung_m": "Peak absolute sprung displacement at the selected ratio (m)",
    "damped_sweep_selected_peak_abs_load_variation_N": "Peak absolute tire load variation at the selected ratio (N)",
}
for _ratio in DAMPING_RATIOS:
    OUTPUTS[f"damped_sweep_zeta_{ratio_key(_ratio)}_peak_abs_sprung_m"] = "Peak absolute sprung displacement (m)"
    OUTPUTS[f"damped_sweep_zeta_{ratio_key(_ratio)}_peak_abs_load_variation_N"] = "Peak absolute tire load variation (N)"


def main(parameters):
    ms, ks, selected_damping, critical, selected_ratio = system_settings(parameters, quarter_car=True)
    mu, kt = parameters["mu"], parameters["Kt"]
    times = np.linspace(0, SIMULATION_TIME_S, OUTPUT_SAMPLES)
    static_load = (ms + mu) * GRAVITY_M_PER_S2
    figure, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    outputs = {
        "damped_sweep_stiffness_used_N_per_m": float(ks),
        "damped_sweep_critical_coefficient_Ns_per_m": float(critical),
        "damped_sweep_static_tire_load_N": float(static_load),
        "damped_sweep_selected_ratio_used": float(selected_ratio),
        "damped_sweep_selected_coefficient_Ns_per_m": float(selected_damping),
    }
    ratios = sorted(set(DAMPING_RATIOS) | {selected_ratio})
    for ratio in ratios:
        xs, _, xu, _ = quarter_car_response(
            ms, mu, ks, kt, ratio * critical, times, INITIAL_STATE,
            rtol=RK45_RTOL, atol=RK45_ATOL,
        )
        # Preserve the original script's signed tire-load variation convention.
        load_variation = kt * xu
        selected = ratio == selected_ratio
        label = f"zeta = {ratio:g}" + (" (damping_rate best)" if selected else "")
        style = {"label": label, "linewidth": 3.0 if selected else 1.5, "zorder": 5 if selected else 2}
        axes[0].plot(times, xs, **style)
        axes[1].plot(times, load_variation, **style)
        prefix = f"damped_sweep_zeta_{ratio_key(ratio)}"
        peak_sprung = float(np.max(np.abs(xs)))
        peak_load = float(np.max(np.abs(load_variation)))
        if ratio in DAMPING_RATIOS:
            outputs[f"{prefix}_peak_abs_sprung_m"] = peak_sprung
            outputs[f"{prefix}_peak_abs_load_variation_N"] = peak_load
        if selected:
            outputs["damped_sweep_selected_peak_abs_sprung_m"] = peak_sprung
            outputs["damped_sweep_selected_peak_abs_load_variation_N"] = peak_load
    axes[0].set(ylabel="Sprung displacement (m)", title="Quarter-car damping-ratio sweep")
    axes[1].set(xlabel="Time (s)", ylabel="Tire load variation (N)", title="Dynamic tire-load variation")
    for axis in axes:
        axis.grid(True)
        axis.legend()
    figure.tight_layout()
    print(f"Suspension stiffness from Tire stiffness: Ks = {ks:.6f} N/m")
    print(f"Quarter sprung mass: {ms:g} kg; static tire load: {static_load:.6f} N")
    print(f"Selected damping_rate_best_ratio: {selected_ratio:g}; damping coefficient: {selected_damping:.6f} N s/m")
    print(f"Damping ratios: {ratios}; reference critical damping: {critical:.6f} N s/m")
    return figure, outputs
