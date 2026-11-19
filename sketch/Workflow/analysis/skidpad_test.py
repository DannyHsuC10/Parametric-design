"""Estimate speed, lateral acceleration, and downforce over skidpad lap times."""

TITLE = "skidpad_test"
DESCRIPTION = "Calculate skidpad performance and the downforce required across lap times."
PLUGIN_ID = "skidpad_test"
PARAMETERS = {
    "ms": "float",
    "mu": "float",
    "wl_mu_y": "float",
    "target_lap_time_s": "float",
}
OUTPUTS = {
    "F_ref": "Required downforce at the target skidpad lap time (N)",
    "v_ref": "Vehicle speed at the target skidpad lap time (km/h)",
    "skidpad_target_lap_time_s": "Target skidpad lap time (s)",
    "skidpad_target_downforce_N": "Required downforce at the target skidpad lap time (N)",
    "skidpad_target_required_mu": "Required friction coefficient at the target lap time",
}

import matplotlib.pyplot as plt
import numpy as np


def main(parameters):
    sprung_mass = parameters["ms"]
    unsprung_mass = parameters["mu"]
    tire_friction = parameters["wl_mu_y"]
    target_lap_time = parameters["target_lap_time_s"]
    if sprung_mass <= 0 or unsprung_mass <= 0 or tire_friction <= 0:
        raise ValueError("ms, mu, and wl_mu_y must be greater than zero")
    if not 4.0 <= target_lap_time <= 6.0:
        raise ValueError("target_lap_time_s must be between 4.0 and 6.0 seconds")

    mass = sprung_mass + 4 * unsprung_mass
    diameter = 18.25
    gravity = 9.81
    factor = 1.4
    radius = diameter / 2
    circumference = np.pi * diameter
    lap_time = np.linspace(4.0, 6.0, 200)
    speed = circumference / lap_time
    speed_kmh = speed * 3.6
    lateral_acceleration = speed**2 / radius
    required_mu = lateral_acceleration / gravity * factor
    downforce = (required_mu / tire_friction - 1) * mass * gravity

    marker_times = np.array([5.5, 5.3, 5.0, 4.8, 4.6])
    marker_indices = [int(np.argmin(np.abs(lap_time - value))) for value in marker_times]
    target_speed = circumference / target_lap_time
    target_speed_kmh = target_speed * 3.6
    target_lateral_acceleration = target_speed**2 / radius
    target_required_mu = target_lateral_acceleration / gravity * factor
    target_downforce = (target_required_mu / tire_friction - 1) * mass * gravity
    figure, axes = plt.subplots(2, 2, figsize=(12, 8))
    panels = [
        (axes[0, 0], speed_kmh, "Vehicle Speed", "Speed (km/h)", lambda i: f"{speed_kmh[i]:.1f} km/h", target_speed_kmh),
        (axes[0, 1], lateral_acceleration / gravity, "Lateral Acceleration", "Acceleration (g)", lambda i: f"{lateral_acceleration[i] / gravity:.2f} g", target_lateral_acceleration / gravity),
        (axes[1, 0], required_mu, "Required Friction Coefficient", "μ", lambda i: f"μ={required_mu[i]:.2f}", target_required_mu),
        (axes[1, 1], downforce, "Required Downforce", "Downforce (N)", lambda i: f"{downforce[i]:.0f} N", target_downforce),
    ]
    for axis, values, title, ylabel, annotation, target_value in panels:
        axis.plot(lap_time, values, linewidth=2)
        axis.scatter(lap_time[marker_indices], values[marker_indices], color="red", zorder=5)
        for marker_time, index in zip(marker_times, marker_indices):
            axis.annotate(
                f"{marker_time:.1f}s\n{annotation(index)}",
                (lap_time[index], values[index]),
                xytext=(5, 8),
                textcoords="offset points",
                fontsize=9,
            )
        axis.scatter(
            [target_lap_time],
            [target_value],
            color="darkorange",
            marker="*",
            s=130,
            zorder=6,
            label=f"Target {target_lap_time:.2f} s",
        )
        axis.legend()
        axis.grid(True)
        axis.set_title(title)
        axis.set_xlabel("Lap Time (s)")
        axis.set_ylabel(ylabel)
    axes[1, 0].axhline(tire_friction, color="red", linestyle="--", label="Tire μ")
    axes[1, 0].legend()
    figure.tight_layout()

    print(f"Target lap time: {target_lap_time:.2f} s")
    print(f"Target speed: {target_speed_kmh:.2f} km/h")
    print(f"Required friction coefficient: {target_required_mu:.3f}")
    print(f"Required downforce at target lap time: {target_downforce:.3f} N")
    return figure, {
        "F_ref": float(target_downforce),
        "v_ref": float(target_speed_kmh),
        "skidpad_target_lap_time_s": float(target_lap_time),
        "skidpad_target_downforce_N": float(target_downforce),
        "skidpad_target_required_mu": float(target_required_mu),
    }
