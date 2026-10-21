"""Compare explicit Euler response and energy drift at different time steps."""

TITLE = "Time_sensitivity"
DESCRIPTION = "Compare explicit Euler time steps using the spring stiffness from Tire stiffness."
PLUGIN_ID = "time_sensitivity"
PARAMETERS = {
    "ms": "float",
    "Ks": "float",
}
HIDDEN_PARAMETERS = {"Ks"}
OUTPUTS = {
    "simulation_sensitivity_mass_used_kg": "Quarter sprung mass used in the time-step sweep (kg)",
    "simulation_sensitivity_stiffness_used_N_per_m": "Spring stiffness Ks supplied by Tire stiffness (N/m)",
    "simulation_sensitivity_finest_dt_s": "Smallest tested Euler time step (s)",
    "simulation_sensitivity_finest_final_energy_error_percent": "Final energy error at the finest step (%)",
    "simulation_sensitivity_coarsest_final_energy_error_percent": "Final energy error at the coarsest step (%)",
    "simulation_sensitivity_finest_max_abs_error_m": "Maximum displacement error at the finest step (m)",
}

# Fixed simulation settings; stiffness is supplied by the upstream analysis.
INITIAL_DISPLACEMENT_M = 0.05
INITIAL_VELOCITY_M_PER_S = 0.0
SIMULATION_TIME_S = 5.0
TIME_STEPS_S = (0.01, 0.001, 0.0001, 0.00001)

import matplotlib.pyplot as plt
import numpy as np
from analysis_result import AnalysisResult

from oscillation_models import (
    analytical_response,
    energy_error_percent,
    explicit_euler,
    oscillator_energy,
    require_positive,
    time_grid,
)


def main(parameters):
    require_positive(parameters, "ms", "Ks")
    mass = parameters["ms"] / 4
    stiffness = parameters["Ks"]
    x0, v0 = INITIAL_DISPLACEMENT_M, INITIAL_VELOCITY_M_PER_S
    steps = sorted(set(TIME_STEPS_S), reverse=True)
    responses = []
    for step in steps:
        times = time_grid(SIMULATION_TIME_S, step)
        displacement, velocity = explicit_euler(mass, stiffness, x0, v0, times)
        energy = oscillator_energy(mass, stiffness, displacement, velocity)
        error = energy_error_percent(energy)
        exact, _ = analytical_response(mass, stiffness, x0, v0, times)
        responses.append((times, displacement, energy, error, np.max(np.abs(displacement - exact))))

    pages, titles = {}, {}
    for metric_index, (metric, ylabel, label) in enumerate((
        ("displacement", "Displacement (m)", "位移比較"),
        ("energy", "Energy (J)", "總能量比較"),
        ("energy_error", "Energy Error (%)", "能量誤差比較"),
    )):
        for start in range(0, len(steps), 4):
            batch = list(zip(steps, responses))[start:start + 4]
            count = len(batch)
            rows, columns = (1, count) if count <= 2 else (2, 2)
            page, axes = plt.subplots(rows, columns, figsize=(6 * columns, 4 * rows), squeeze=False)
            for axis, (step, response) in zip(axes.flat, batch):
                axis.plot(response[0], response[metric_index + 1])
                axis.set(title=f"Explicit Euler | dt = {step:g} s", xlabel="Time (s)", ylabel=ylabel)
                axis.grid(True)
            for axis in list(axes.flat)[count:]:
                page.delaxes(axis)
            page.suptitle(f"Time-step {metric.replace('_', ' ')} | m = {mass:g} kg | Ks = {stiffness:g} N/m")
            page.tight_layout()
            filename = f"time_step_{metric}_{start // 4 + 1}.png"
            pages[filename] = page
            titles[filename] = label + (f"（第 {start // 4 + 1} 組）" if len(steps) > 4 else "")
    primary = next(iter(pages))
    figure = pages.pop(primary)
    titles["plot.png"] = "主要結果｜" + titles.pop(primary)

    print(f"Quarter sprung mass: {mass:.3f} kg (total sprung mass / 4)")
    print(f"Spring stiffness from Tire stiffness: Ks = {stiffness:.6f} N/m")
    for step, response in zip(steps, responses):
        print(f"dt = {step:g} s: final energy error = {response[3][-1]:.6g}%, "
              f"maximum displacement error = {response[4]:.8g} m")
    return AnalysisResult(figure, {
        "simulation_sensitivity_mass_used_kg": float(mass),
        "simulation_sensitivity_stiffness_used_N_per_m": float(stiffness),
        "simulation_sensitivity_finest_dt_s": float(steps[-1]),
        "simulation_sensitivity_finest_final_energy_error_percent": float(responses[-1][3][-1]),
        "simulation_sensitivity_coarsest_final_energy_error_percent": float(responses[0][3][-1]),
        "simulation_sensitivity_finest_max_abs_error_m": float(responses[-1][4]),
    }, figures=pages, figure_titles=titles)
