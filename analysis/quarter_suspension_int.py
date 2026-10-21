"""Semi-implicit Euler quarter-car response starting from static equilibrium."""

import matplotlib.pyplot as plt
import numpy as np

from damping_models import QUARTER_CAR_PARAMETERS, print_settings, system_settings
from oscillation_models import time_grid

TITLE = "quarter_suspension_int"
PLUGIN_ID = "quarter_suspension_int"
DESCRIPTION = "Quarter-car road-step response using semi-implicit Euler and gravity."
PARAMETERS = dict(QUARTER_CAR_PARAMETERS)
HIDDEN_PARAMETERS = {"Ks", "damping_rate_best_ratio"}
OUTPUTS = {
    "quarter_int_stiffness_used_N_per_m": "Suspension spring stiffness Ks (N/m)",
    "quarter_int_coefficient_Ns_per_m": "Suspension damping coefficient (N s/m)",
    "quarter_int_ratio_used": "Selected damping ratio supplied by damping_rate",
    "quarter_int_static_sprung_position_m": "Initial static sprung position (m)",
    "quarter_int_max_sprung_position_m": "Maximum absolute-coordinate sprung position (m)",
    "quarter_int_max_sprung_acceleration_m_per_s2": "Maximum signed sprung acceleration (m/s^2)",
    "quarter_int_peak_abs_sprung_acceleration_m_per_s2": "Peak absolute sprung acceleration (m/s^2)",
}

GRAVITY_M_PER_S2 = 9.81
INITIAL_VELOCITIES_M_PER_S = (0.0, 0.0)
SIMULATION_TIME_S = 5.0
TIME_STEP_S = 0.001
ROAD_STEP_TIME_S = 1.0
ROAD_STEP_HEIGHT_M = 0.05


def main(parameters):
    ms, ks, damping, _, ratio = system_settings(parameters, quarter_car=True)
    mu, kt = parameters["mu"], parameters["Kt"]
    times = time_grid(SIMULATION_TIME_S, TIME_STEP_S)
    zu = -(ms + mu) * GRAVITY_M_PER_S2 / kt
    zs = zu - ms * GRAVITY_M_PER_S2 / ks
    static_position = zs
    vs, vu = INITIAL_VELOCITIES_M_PER_S
    positions, accelerations = np.empty(len(times)), np.empty(len(times))
    positions[0], accelerations[0] = zs, 0.0
    try:
        with np.errstate(over="raise", invalid="raise"):
            for index, step in enumerate(np.diff(times)):
                road = ROAD_STEP_HEIGHT_M if times[index] > ROAD_STEP_TIME_S else 0.0
                spring_force, damper_force = ks * (zu - zs), damping * (vu - vs)
                sprung_acceleration = -GRAVITY_M_PER_S2 + (spring_force + damper_force) / ms
                unsprung_acceleration = -GRAVITY_M_PER_S2 + (-spring_force - damper_force + kt * (road - zu)) / mu
                vs += sprung_acceleration * step
                vu += unsprung_acceleration * step
                zs += vs * step
                zu += vu * step
                positions[index + 1] = zs
                accelerations[index + 1] = -GRAVITY_M_PER_S2 + (ks * (zu - zs) + damping * (vu - vs)) / ms
    except FloatingPointError as error:
        raise ValueError("Quarter-car Euler response overflowed; reduce TIME_STEP_S") from error
    if not np.all(np.isfinite(positions)) or not np.all(np.isfinite(accelerations)):
        raise ValueError("Quarter-car Euler response contains non-finite values")
    figure, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    axes[0].plot(times, positions)
    axes[0].axhline(static_position, color="tab:orange", linestyle="--", label="Initial equilibrium")
    axes[0].set(ylabel="Sprung position (m)", title="Quarter Car - Semi-implicit Euler")
    axes[0].legend()
    axes[1].plot(times, accelerations)
    axes[1].set(xlabel="Time (s)", ylabel="Sprung acceleration (m/s²)")
    for axis in axes:
        axis.axvline(ROAD_STEP_TIME_S, color="gray", linestyle="--")
        axis.grid(True)
    figure.tight_layout()
    print_settings(ms, ks, damping, ratio, "Suspension stiffness Ks")
    print(f"Initial static sprung position: {static_position:.8g} m")
    print(f"Maximum sprung position: {np.max(positions):.8g} m")
    print(f"Peak absolute sprung acceleration: {np.max(np.abs(accelerations)):.8g} m/s²")
    return figure, {
        "quarter_int_stiffness_used_N_per_m": float(ks),
        "quarter_int_coefficient_Ns_per_m": float(damping),
        "quarter_int_ratio_used": float(ratio),
        "quarter_int_static_sprung_position_m": float(static_position),
        "quarter_int_max_sprung_position_m": float(np.max(positions)),
        "quarter_int_max_sprung_acceleration_m_per_s2": float(np.max(accelerations)),
        "quarter_int_peak_abs_sprung_acceleration_m_per_s2": float(np.max(np.abs(accelerations))),
    }
