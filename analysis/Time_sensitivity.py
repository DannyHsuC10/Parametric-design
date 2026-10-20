"""Compare explicit Euler response and energy drift at different time steps."""

TITLE = "Time_sensitivity"
DESCRIPTION = "Compare explicit Euler time steps using the spring stiffness from Tire stiffness."
PLUGIN_ID = "time_sensitivity"
PARAMETERS = {
    "simulation_ms_total_kg": "float",
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

from oscillation_models import (
    analytical_response,
    energy_error_percent,
    explicit_euler,
    oscillator_energy,
    require_positive,
    time_grid,
)


def main(parameters):
    require_positive(parameters, "simulation_ms_total_kg", "Ks")
    mass = parameters["simulation_ms_total_kg"] / 4
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

    figure, axes = plt.subplots(3, len(steps), figsize=(max(8, 4 * len(steps)), 9),
                                sharex="col", squeeze=False)
    for column, (step, response) in enumerate(zip(steps, responses)):
        times, displacement, energy, error, _ = response
        for row, values in enumerate((displacement, energy, error)):
            axes[row, column].plot(times, values)
            axes[row, column].grid(True)
        axes[0, column].set_title(f"Explicit Euler | dt = {step:g} s")
        axes[2, column].set_xlabel("Time (s)")
    for row, label in enumerate(("Displacement (m)", "Energy (J)", "Energy Error (%)")):
        axes[row, 0].set_ylabel(label)
    figure.suptitle(f"Time-step sensitivity | quarter sprung mass = {mass:g} kg | Ks = {stiffness:g} N/m")
    figure.tight_layout(rect=[0, 0, 1, 0.96])

    print(f"Quarter sprung mass: {mass:.3f} kg (total sprung mass / 4)")
    print(f"Spring stiffness from Tire stiffness: Ks = {stiffness:.6f} N/m")
    for step, response in zip(steps, responses):
        print(f"dt = {step:g} s: final energy error = {response[3][-1]:.6g}%, "
              f"maximum displacement error = {response[4]:.8g} m")
    return figure, {
        "simulation_sensitivity_mass_used_kg": float(mass),
        "simulation_sensitivity_stiffness_used_N_per_m": float(stiffness),
        "simulation_sensitivity_finest_dt_s": float(steps[-1]),
        "simulation_sensitivity_finest_final_energy_error_percent": float(responses[-1][3][-1]),
        "simulation_sensitivity_coarsest_final_energy_error_percent": float(responses[0][3][-1]),
        "simulation_sensitivity_finest_max_abs_error_m": float(responses[-1][4]),
    }
