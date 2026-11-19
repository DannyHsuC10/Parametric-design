"""Explicit Euler integration of a damped SDOF model with gravity."""

import matplotlib.pyplot as plt
import numpy as np

from .suspension_dynamics.damping_models import SINGLE_DOF_PARAMETERS, print_settings, system_settings
from .suspension_dynamics.oscillation_models import time_grid

TITLE = "damping_int"
PLUGIN_ID = "damping_int"
DESCRIPTION = "Explicit Euler displacement with gravity using the equivalent ride stiffness."
PARAMETERS = dict(SINGLE_DOF_PARAMETERS)
HIDDEN_PARAMETERS = {"Ks", "damping_rate_best_ratio"}
OUTPUTS = {
    "damping_int_ride_stiffness_N_per_m": "Equivalent ride stiffness Kr (N/m)",
    "damping_int_coefficient_Ns_per_m": "Damping coefficient (N s/m)",
    "damping_int_ratio_used": "Selected damping ratio supplied by damping_rate",
    "damping_int_equilibrium_m": "Static equilibrium displacement including gravity (m)",
    "damping_int_final_displacement_m": "Displacement at the final simulation time (m)",
    "damping_int_peak_abs_displacement_m": "Maximum absolute displacement (m)",
}

GRAVITY_M_PER_S2 = 9.81
INITIAL_DISPLACEMENT_M = 0.1
INITIAL_VELOCITY_M_PER_S = 0.0
SIMULATION_TIME_S = 10.0
TIME_STEP_S = 0.01


def main(parameters):
    mass, stiffness, damping, _, ratio = system_settings(parameters)
    times = time_grid(SIMULATION_TIME_S, TIME_STEP_S)
    displacement, velocity = np.empty(len(times)), np.empty(len(times))
    displacement[0], velocity[0] = INITIAL_DISPLACEMENT_M, INITIAL_VELOCITY_M_PER_S
    try:
        with np.errstate(over="raise", invalid="raise"):
            for index, step in enumerate(np.diff(times)):
                acceleration = (-damping * velocity[index] - stiffness * displacement[index]) / mass - GRAVITY_M_PER_S2
                velocity[index + 1] = velocity[index] + acceleration * step
                displacement[index + 1] = displacement[index] + velocity[index] * step
    except FloatingPointError as error:
        raise ValueError("Damped Euler response overflowed; reduce TIME_STEP_S in damping_int.py") from error
    if not np.all(np.isfinite(displacement)) or not np.all(np.isfinite(velocity)):
        raise ValueError("Damped Euler response contains non-finite values")
    equilibrium = -mass * GRAVITY_M_PER_S2 / stiffness
    figure, axis = plt.subplots(figsize=(9, 5))
    axis.plot(times, displacement, label="Explicit Euler")
    axis.axhline(equilibrium, color="tab:orange", linestyle="--", label="Static equilibrium")
    axis.set(xlabel="Time (s)", ylabel="Displacement (m)",
             title=f"Damped Euler with gravity | dt = {TIME_STEP_S:g} s")
    axis.grid(True)
    axis.legend()
    figure.tight_layout()
    print_settings(mass, stiffness, damping, ratio, "Equivalent ride stiffness Kr")
    print(f"Static equilibrium: {equilibrium:.8g} m")
    return figure, {
        "damping_int_ride_stiffness_N_per_m": float(stiffness),
        "damping_int_coefficient_Ns_per_m": float(damping),
        "damping_int_ratio_used": float(ratio),
        "damping_int_equilibrium_m": float(equilibrium),
        "damping_int_final_displacement_m": float(displacement[-1]),
        "damping_int_peak_abs_displacement_m": float(np.max(np.abs(displacement))),
    }
