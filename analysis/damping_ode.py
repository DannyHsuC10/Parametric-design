"""Damped SDOF response and phase portrait with adaptive RK45."""

import matplotlib.pyplot as plt
import numpy as np

from damping_models import SINGLE_DOF_PARAMETERS, checked_solution, print_settings, system_settings

TITLE = "damping_ode"
PLUGIN_ID = "damping_ode"
DESCRIPTION = "Damped SDOF displacement and phase portrait using equivalent ride stiffness."
PARAMETERS = dict(SINGLE_DOF_PARAMETERS)
HIDDEN_PARAMETERS = {"Ks", "damping_rate_best_ratio"}
OUTPUTS = {
    "damping_ode_ride_stiffness_N_per_m": "Equivalent ride stiffness Kr (N/m)",
    "damping_ode_coefficient_Ns_per_m": "Damping coefficient (N s/m)",
    "damping_ode_natural_frequency_Hz": "Undamped natural frequency of the SDOF model (Hz)",
    "damping_ode_ratio_used": "Damping ratio used in the solver",
    "damping_ode_final_displacement_m": "Final equilibrium-relative displacement (m)",
}

INITIAL_STATE = (1.0, 0.0)
SIMULATION_TIME_S = 20.0
OUTPUT_SAMPLES = 4001
RK45_RTOL = 0.000001
RK45_ATOL = 0.00000001


def main(parameters):
    mass, stiffness, damping, _, ratio = system_settings(parameters)
    times = np.linspace(0, SIMULATION_TIME_S, OUTPUT_SAMPLES)

    def rhs(time, state):
        displacement, velocity = state
        return [velocity, -(damping * velocity + stiffness * displacement) / mass]

    displacement, velocity = checked_solution(rhs, times, INITIAL_STATE, RK45_RTOL, RK45_ATOL)
    frequency = np.sqrt(stiffness / mass) / (2 * np.pi)
    figure, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].plot(times, displacement)
    axes[0].set(xlabel="Time (s)", ylabel="Displacement (m)",
                title=f"Damped response | zeta = {ratio:g}, fn = {frequency:.3f} Hz")
    axes[1].plot(displacement, velocity)
    axes[1].set(xlabel="Displacement (m)", ylabel="Velocity (m/s)", title="Phase portrait")
    for axis in axes:
        axis.grid(True)
    figure.tight_layout()
    print_settings(mass, stiffness, damping, ratio, "Equivalent ride stiffness Kr")
    case = "Critically damped" if np.isclose(ratio, 1.0, rtol=0, atol=1e-6) else (
        "Underdamped" if ratio < 1 else "Overdamped")
    print(f"Case: {case}")
    return figure, {
        "damping_ode_ride_stiffness_N_per_m": float(stiffness),
        "damping_ode_coefficient_Ns_per_m": float(damping),
        "damping_ode_natural_frequency_Hz": float(frequency),
        "damping_ode_ratio_used": float(ratio),
        "damping_ode_final_displacement_m": float(displacement[-1]),
    }
