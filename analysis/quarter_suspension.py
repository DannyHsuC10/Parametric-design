"""Damped quarter-car road-step response using adaptive RK45."""

import matplotlib.pyplot as plt
import numpy as np

from .suspension_dynamics.damping_models import QUARTER_CAR_PARAMETERS, print_settings, quarter_car_response, system_settings

TITLE = "quarter_suspension"
PLUGIN_ID = "quarter_suspension"
DESCRIPTION = "Damped quarter-car road-step displacement, velocity, acceleration and energy."
PARAMETERS = dict(QUARTER_CAR_PARAMETERS)
HIDDEN_PARAMETERS = {"Ks", "damping_rate_best_ratio"}
OUTPUTS = {
    "quarter_ode_stiffness_used_N_per_m": "Suspension spring stiffness Ks (N/m)",
    "quarter_ode_critical_coefficient_Ns_per_m": "Sprung-mass reference critical damping (N s/m)",
    "quarter_ode_coefficient_Ns_per_m": "Suspension damping coefficient (N s/m)",
    "quarter_ode_ratio_used": "Selected damping ratio supplied by damping_rate",
    "quarter_ode_peak_abs_sprung_acceleration_m_per_s2": "Peak absolute sprung acceleration (m/s^2)",
    "quarter_ode_final_sprung_displacement_m": "Final equilibrium-relative sprung displacement (m)",
    "quarter_ode_final_energy_J": "Final kinetic and elastic energy using road-relative tire deformation (J)",
}

INITIAL_STATE = (0.0, 0.0, 0.0, 0.0)
SIMULATION_TIME_S = 1.0
OUTPUT_SAMPLES = 2000
ROAD_STEP_TIME_S = 0.1
ROAD_STEP_HEIGHT_M = 0.05
RK45_RTOL = 0.0000001
RK45_ATOL = 0.000000001


def main(parameters):
    ms, ks, damping, critical, ratio = system_settings(parameters, quarter_car=True)
    mu, kt = parameters["mu"], parameters["Kt"]
    times = np.linspace(0, SIMULATION_TIME_S, OUTPUT_SAMPLES)
    xs, vs, xu, vu = quarter_car_response(
        ms, mu, ks, kt, damping, times, INITIAL_STATE,
        road_height=ROAD_STEP_HEIGHT_M, road_step_time=ROAD_STEP_TIME_S,
        rtol=RK45_RTOL, atol=RK45_ATOL,
    )
    road = np.where(times >= ROAD_STEP_TIME_S, ROAD_STEP_HEIGHT_M, 0.0)
    force = ks * (xs - xu) + damping * (vs - vu)
    sprung_acceleration = -force / ms
    unsprung_acceleration = (force - kt * (xu - road)) / mu
    energy = (0.5 * ms * vs**2 + 0.5 * mu * vu**2
              + 0.5 * ks * (xs - xu)**2 + 0.5 * kt * (xu - road)**2)
    figure, axes = plt.subplots(4, 1, figsize=(10, 12), sharex=True)
    for axis, sprung, unsprung, label in zip(
        axes[:3], (xs, vs, sprung_acceleration), (xu, vu, unsprung_acceleration),
        ("Position (m)", "Velocity (m/s)", "Acceleration (m/s²)"),
    ):
        axis.plot(times, sprung, label="Sprung")
        axis.plot(times, unsprung, "--", label="Unsprung")
        axis.set_ylabel(label)
        axis.legend()
    axes[0].plot(times, road, ":", color="gray", label="Road")
    axes[0].legend()
    axes[0].set_title(f"Quarter Car - RK45 | zeta = {ratio:g}")
    axes[3].plot(times, energy)
    axes[3].set(xlabel="Time (s)", ylabel="Energy (J)", title="Kinetic and elastic energy")
    for axis in axes:
        axis.grid(True)
    figure.tight_layout()
    print_settings(ms, ks, damping, ratio, "Suspension stiffness Ks")
    print(f"Reference critical damping: {critical:.6f} N s/m")
    print(f"Peak absolute sprung acceleration: {np.max(np.abs(sprung_acceleration)):.8g} m/s²")
    return figure, {
        "quarter_ode_stiffness_used_N_per_m": float(ks),
        "quarter_ode_critical_coefficient_Ns_per_m": float(critical),
        "quarter_ode_coefficient_Ns_per_m": float(damping),
        "quarter_ode_ratio_used": float(ratio),
        "quarter_ode_peak_abs_sprung_acceleration_m_per_s2": float(np.max(np.abs(sprung_acceleration))),
        "quarter_ode_final_sprung_displacement_m": float(xs[-1]),
        "quarter_ode_final_energy_J": float(energy[-1]),
    }
