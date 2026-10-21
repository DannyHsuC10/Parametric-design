"""Compare the exact undamped oscillator response with explicit Euler."""

TITLE = "Analytical_Numerical_Simulation"
DESCRIPTION = "Compare analytical and explicit Euler responses using Ks from Tire stiffness."
PLUGIN_ID = "analytical_numerical_simulation"
PARAMETERS = {
    "ms": "float",
    "Ks": "float",
}
HIDDEN_PARAMETERS = {"Ks"}
OUTPUTS = {
    "simulation_corner_mass_kg": "One-quarter of the configured total sprung mass (kg)",
    "simulation_euler_stiffness_used_N_per_m": "Spring stiffness Ks supplied by Tire stiffness (N/m)",
    "simulation_natural_frequency_Hz": "Undamped single-degree-of-freedom natural frequency (Hz)",
    "simulation_euler_max_abs_error_m": "Maximum absolute Euler displacement error (m)",
    "simulation_euler_rms_error_m": "RMS Euler displacement error (m)",
    "simulation_euler_max_relative_error_percent": "Maximum pointwise relative displacement error (%)",
    "simulation_euler_final_energy_error_percent": "Euler total energy change at the final time (%)",
}

# Fixed simulation settings; stiffness is supplied by Tire stiffness.
INITIAL_DISPLACEMENT_M = 0.05
INITIAL_VELOCITY_M_PER_S = 0.0
SIMULATION_TIME_S = 5.0
TIME_STEP_S = 0.00001

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
    require_positive(parameters, "ms", "Ks")
    mass = parameters["ms"] / 4
    stiffness = parameters["Ks"]
    times = time_grid(SIMULATION_TIME_S, TIME_STEP_S)
    x0, v0 = INITIAL_DISPLACEMENT_M, INITIAL_VELOCITY_M_PER_S
    analytical, _ = analytical_response(mass, stiffness, x0, v0, times)
    numerical, velocity = explicit_euler(mass, stiffness, x0, v0, times)
    absolute_error = np.abs(numerical - analytical)
    relative_error = absolute_error / (np.abs(analytical) + 1e-12) * 100
    energy_error = energy_error_percent(oscillator_energy(mass, stiffness, numerical, velocity))
    frequency = np.sqrt(stiffness / mass) / (2 * np.pi)

    figure, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
    axes[0].plot(times, analytical, linewidth=2, label="Analytical")
    axes[0].plot(times, numerical, "--", linewidth=1.5, label="Explicit Euler")
    axes[0].set_title(f"Analytical vs Numerical | m = {mass:g} kg, f = {frequency:.3f} Hz")
    axes[0].set_ylabel("Displacement (m)")
    axes[0].legend()
    axes[1].plot(times, absolute_error)
    axes[1].set_ylabel("Absolute Error (m)")
    axes[2].plot(times, relative_error)
    axes[2].set_ylabel("Relative Error (%)")
    axes[2].set_xlabel("Time (s)")
    for axis in axes:
        axis.grid(True)
    figure.tight_layout()

    print(f"Quarter sprung mass: {mass:.3f} kg")
    print(f"Spring stiffness from Tire stiffness: Ks = {stiffness:.6f} N/m")
    print(f"Natural frequency: {frequency:.6f} Hz")
    print(f"Explicit Euler dt: {TIME_STEP_S:g} s")
    print(f"Maximum absolute displacement error: {np.max(absolute_error):.8g} m")
    print(f"Final energy error: {energy_error[-1]:.6f}%")
    return figure, {
        "simulation_corner_mass_kg": float(mass),
        "simulation_euler_stiffness_used_N_per_m": float(stiffness),
        "simulation_natural_frequency_Hz": float(frequency),
        "simulation_euler_max_abs_error_m": float(np.max(absolute_error)),
        "simulation_euler_rms_error_m": float(np.sqrt(np.mean(absolute_error**2))),
        "simulation_euler_max_relative_error_percent": float(np.max(relative_error)),
        "simulation_euler_final_energy_error_percent": float(energy_error[-1]),
    }
