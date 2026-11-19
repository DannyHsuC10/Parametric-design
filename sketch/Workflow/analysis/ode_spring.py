"""Integrate an undamped quarter-car model with adaptive RK45."""

TITLE = "ode_spring"
DESCRIPTION = "Compute quarter-car free vibration with RK45 using Ks from Tire stiffness."
PLUGIN_ID = "ode_spring"
PARAMETERS = {
    "ms": "float",
    "mu": "float",
    "Ks": "float",
}
HIDDEN_PARAMETERS = {"Ks"}
OUTPUTS = {
    "simulation_rk45_stiffness_used_N_per_m": "Suspension spring stiffness Ks supplied by Tire stiffness (N/m)",
    "simulation_rk45_initial_energy_J": "Initial total kinetic and elastic energy (J)",
    "simulation_rk45_max_energy_error_percent": "Maximum absolute total-energy deviation (%)",
    "simulation_rk45_max_sprung_displacement_m": "Maximum absolute sprung displacement (m)",
    "simulation_rk45_max_unsprung_displacement_m": "Maximum absolute unsprung displacement (m)",
}

# Fixed simulation settings; suspension stiffness is supplied by Tire stiffness.
# State order: xs, vs, xu, vu.
TIRE_STIFFNESS_N_PER_M = 100_000.0
INITIAL_STATE = (0.0, 0.0, 0.025, 0.0)
SIMULATION_TIME_S = 5.0
OUTPUT_TIME_STEP_S = 0.001
RK45_RTOL = 0.001
RK45_ATOL = 0.000001

import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import solve_ivp

from .suspension_dynamics.oscillation_models import energy_error_percent, require_positive, time_grid


def main(parameters):
    require_positive(parameters, "ms", "mu", "Ks")
    sprung_mass = parameters["ms"] / 4
    unsprung_mass = parameters["mu"]
    spring_stiffness, tire_stiffness = parameters["Ks"], TIRE_STIFFNESS_N_PER_M
    times = time_grid(SIMULATION_TIME_S, OUTPUT_TIME_STEP_S)

    def quarter_car_ode(time, state):
        xs, vs, xu, vu = state
        spring_force = spring_stiffness * (xs - xu)
        return [vs, -spring_force / sprung_mass,
                vu, (spring_force - tire_stiffness * xu) / unsprung_mass]

    solution = solve_ivp(quarter_car_ode, (0, SIMULATION_TIME_S), INITIAL_STATE,
                         t_eval=times, method="RK45", rtol=RK45_RTOL, atol=RK45_ATOL)
    if not solution.success or not np.all(np.isfinite(solution.y)):
        raise RuntimeError(f"Quarter-car RK45 solver failed: {solution.message}")
    xs, vs, xu, vu = solution.y
    energy = (0.5 * sprung_mass * vs**2 + 0.5 * unsprung_mass * vu**2
              + 0.5 * spring_stiffness * (xs - xu)**2 + 0.5 * tire_stiffness * xu**2)
    error = energy_error_percent(energy)

    figure, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
    axes[0].plot(solution.t, xs, linewidth=2, label="Sprung")
    axes[0].plot(solution.t, xu, "--", linewidth=1.5, label="Unsprung")
    axes[0].set_ylabel("Position (m)")
    axes[0].set_title("Quarter Car (No Damping) - RK45")
    axes[0].legend()
    axes[1].plot(solution.t, energy)
    axes[1].set_ylabel("Total Energy (J)")
    axes[2].plot(solution.t, error)
    axes[2].set_ylabel("Energy Error (%)")
    axes[2].set_xlabel("Time (s)")
    for axis in axes:
        axis.grid(True)
    figure.tight_layout()

    print(f"Quarter sprung mass: {sprung_mass:.3f} kg; unsprung mass: {unsprung_mass:.3f} kg")
    print(f"Spring stiffness from Tire stiffness: Ks = {spring_stiffness:.6f} N/m")
    print(f"Initial energy: {energy[0]:.8g} J")
    print(f"Maximum absolute energy error: {np.max(np.abs(error)):.6f}%")
    print(f"RK45 uses adaptive internal steps; output sampling interval: {OUTPUT_TIME_STEP_S:g} s.")
    return figure, {
        "simulation_rk45_stiffness_used_N_per_m": float(spring_stiffness),
        "simulation_rk45_initial_energy_J": float(energy[0]),
        "simulation_rk45_max_energy_error_percent": float(np.max(np.abs(error))),
        "simulation_rk45_max_sprung_displacement_m": float(np.max(np.abs(xs))),
        "simulation_rk45_max_unsprung_displacement_m": float(np.max(np.abs(xu))),
    }
