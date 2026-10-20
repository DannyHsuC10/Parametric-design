"""Rank damping ratios using six normalized ride and dissipation metrics."""

import matplotlib.pyplot as plt
import numpy as np

from damping_models import SINGLE_DOF_PARAMETERS, checked_solution, system_settings
from oscillation_models import oscillator_energy

TITLE = "damping_rate"
PLUGIN_ID = "damping_rate"
DESCRIPTION = "Compare damping-ratio responses, six performance metrics and normalized weighted scores."
PARAMETERS = {name: kind for name, kind in SINGLE_DOF_PARAMETERS.items()
              if name != "damping_rate_best_ratio"}
HIDDEN_PARAMETERS = {"Ks"}

DAMPING_RATIOS = (0.1, 0.3, 0.5, 0.7, 0.9)
INITIAL_STATE = (0.05, 0.0)
SIMULATION_TIME_S = 1.0
OUTPUT_SAMPLES = 1000
SETTLING_FRACTION = 0.05
DISSIPATED_ENERGY_FRACTION = 0.95
RK45_RTOL = 0.001
RK45_ATOL = 0.000001
SCORE_METRICS = (
    "first_cross_s", "overshoot_m", "rms_acceleration_m_per_s2",
    "peak_acceleration_m_per_s2", "ride_recovery_s", "energy95_time_s",
)
SCORE_WEIGHTS = (1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
METRIC_NAMES = (
    "first_cross_s", "overshoot_m", "rms_displacement_m", "rms_acceleration_m_per_s2",
    "peak_acceleration_m_per_s2", "ride_recovery_s", "peak_dissipation_power_W",
    "energy95_time_s", "normalized_score",
)


def ratio_key(ratio):
    return f"{ratio:.1f}".replace(".", "p")


OUTPUTS = {
    "damping_rate_ride_stiffness_N_per_m": "Equivalent ride stiffness Kr (N/m)",
    "damping_rate_critical_coefficient_Ns_per_m": "SDOF critical damping based on Kr (N s/m)",
    "damping_rate_best_ratio": "Lowest-cost tested damping ratio",
    "damping_rate_best_coefficient_Ns_per_m": "Damping coefficient at the lowest-cost tested ratio (N s/m)",
    "damping_rate_best_score": "Lowest normalized weighted score",
}
for _ratio in DAMPING_RATIOS:
    for _metric in METRIC_NAMES:
        OUTPUTS[f"damping_rate_zeta_{ratio_key(_ratio)}_{_metric}"] = (
            f"{_metric} for zeta={_ratio:g}; -1 means timing not reached within simulation"
        )


def normalized_cost(values):
    """Unreached timing metrics receive the worst cost, without poisoning scores."""
    values = np.asarray(values, dtype=float)
    finite = np.isfinite(values)
    result = np.ones_like(values)
    if np.any(finite):
        lower, upper = np.min(values[finite]), np.max(values[finite])
        result[finite] = 0.0 if np.isclose(upper, lower) else (values[finite] - lower) / (upper - lower)
    return result


def response_metrics(times, displacement, velocity, acceleration, mass, stiffness, damping):
    crossings = np.flatnonzero((displacement[:-1] * displacement[1:] < 0) | (displacement[1:] == 0))
    first_cross, overshoot = np.nan, 0.0
    if len(crossings):
        index = crossings[0]
        fraction = abs(displacement[index]) / (abs(displacement[index]) + abs(displacement[index + 1]))
        first_cross = times[index] + fraction * (times[index + 1] - times[index])
        overshoot = float(np.max(np.abs(displacement[index + 1:])))
    outside = np.flatnonzero(np.abs(displacement) > SETTLING_FRACTION * abs(INITIAL_STATE[0]))
    recovery_index = outside[-1] + 1 if len(outside) else 0
    recovery = times[recovery_index] if recovery_index < len(times) else np.nan
    energy = oscillator_energy(mass, stiffness, displacement, velocity)
    dissipated = energy[0] - energy
    energy_indices = np.flatnonzero(dissipated >= DISSIPATED_ENERGY_FRACTION * energy[0])
    energy_time = times[energy_indices[0]] if len(energy_indices) else np.nan
    return {
        "first_cross_s": float(first_cross),
        "overshoot_m": overshoot,
        "rms_displacement_m": float(np.sqrt(np.mean(displacement**2))),
        "rms_acceleration_m_per_s2": float(np.sqrt(np.mean(acceleration**2))),
        "peak_acceleration_m_per_s2": float(np.max(np.abs(acceleration))),
        "ride_recovery_s": float(recovery),
        "peak_dissipation_power_W": float(np.max(damping * velocity**2)),
        "energy95_time_s": float(energy_time),
    }


def main(parameters):
    mass, stiffness, _, critical, _ = system_settings(parameters, damping_ratio=0.0)
    times = np.linspace(0, SIMULATION_TIME_S, OUTPUT_SAMPLES)
    figure = plt.figure(figsize=(14, 22))
    grid = figure.add_gridspec(7, 2, height_ratios=(1, 1, 1, 0.8, 0.8, 0.8, 1.3))
    response_axes = [figure.add_subplot(grid[row, :]) for row in range(3)]
    metric_axes = [figure.add_subplot(grid[row, column]) for row in range(3, 6) for column in range(2)]
    score_axis = figure.add_subplot(grid[6, :])
    metrics = []
    for ratio in DAMPING_RATIOS:
        damping = ratio * critical

        def rhs(time, state):
            displacement, velocity = state
            return [velocity, -(damping * velocity + stiffness * displacement) / mass]

        displacement, velocity = checked_solution(rhs, times, INITIAL_STATE, RK45_RTOL, RK45_ATOL)
        acceleration = -(damping * velocity + stiffness * displacement) / mass
        metrics.append(response_metrics(times, displacement, velocity, acceleration, mass, stiffness, damping))
        for axis, values in zip(response_axes, (displacement, velocity, acceleration)):
            axis.plot(times, values, label=f"zeta = {ratio:.1f}")
    for axis, label in zip(response_axes, ("Displacement (m)", "Velocity (m/s)", "Acceleration (m/s²)")):
        axis.set_ylabel(label)
        axis.set_xlabel("Time (s)")
        axis.grid(True)
    response_axes[0].set_title("Damping-ratio response comparison")
    response_axes[0].legend(ncol=len(DAMPING_RATIOS))
    titles = ("First zero crossing (s)", "Overshoot (m)", "RMS acceleration (m/s²)",
              "Peak acceleration (m/s²)", "Ride height recovery (s)", "95% energy dissipation time (s)")
    normalized = []
    for axis, metric, title in zip(metric_axes, SCORE_METRICS, titles):
        values = np.array([item[metric] for item in metrics])
        axis.plot(DAMPING_RATIOS, values, "o-")
        axis.set(title=title, xlabel="Damping ratio")
        axis.grid(True)
        normalized.append(normalized_cost(values))
    contributions = np.array(normalized) * np.asarray(SCORE_WEIGHTS)[:, None]
    scores = np.sum(contributions, axis=0)
    best = int(np.argmin(scores))
    bottom = np.zeros(len(DAMPING_RATIOS))
    categories = [f"{ratio:.1f}" for ratio in DAMPING_RATIOS]
    for label, contribution in zip(("First", "Overshoot", "RMS", "Peak", "Ride", "Energy"), contributions):
        score_axis.bar(categories, contribution, bottom=bottom, label=label)
        bottom += contribution
    score_axis.set(xlabel="Damping ratio", ylabel="Normalized weighted cost",
                   title=f"Metric contributions | best tested zeta = {DAMPING_RATIOS[best]:.1f}")
    score_axis.legend(ncol=6)
    score_axis.grid(axis="y")
    figure.tight_layout()
    outputs = {
        "damping_rate_ride_stiffness_N_per_m": float(stiffness),
        "damping_rate_critical_coefficient_Ns_per_m": float(critical),
        "damping_rate_best_ratio": float(DAMPING_RATIOS[best]),
        "damping_rate_best_coefficient_Ns_per_m": float(DAMPING_RATIOS[best] * critical),
        "damping_rate_best_score": float(scores[best]),
    }
    for index, (ratio, item) in enumerate(zip(DAMPING_RATIOS, metrics)):
        item["normalized_score"] = float(scores[index])
        for metric in METRIC_NAMES:
            value = item[metric]
            outputs[f"damping_rate_zeta_{ratio_key(ratio)}_{metric}"] = float(value) if np.isfinite(value) else -1.0
        print(f"zeta = {ratio:.1f}: score = {scores[index]:.6g}, recovery = {item['ride_recovery_s']:.6g} s")
    print(f"Equivalent ride stiffness Kr: {stiffness:.6f} N/m; critical damping: {critical:.6f} N s/m")
    print(f"Best tested damping ratio: {DAMPING_RATIOS[best]:.1f}")
    return figure, outputs
