"""Estimate lateral acceleration capability across a downforce sweep."""

TITLE = "Donwforce_Target"
DESCRIPTION = "Show lateral acceleration capability as aerodynamic downforce increases."
PLUGIN_ID = "donwforce_target"
PARAMETERS = {
    "ms": "float",
    "mu": "float",
    "wl_mu_y": "float",
    "skidpad_target_downforce_N": "float",
    "skidpad_target_lap_time_s": "float",
}
HIDDEN_PARAMETERS = {
    "skidpad_target_downforce_N",
    "skidpad_target_lap_time_s",
}
OUTPUTS = {
    "downforce_target_max_lateral_acceleration_g": "Maximum lateral acceleration at the end of the downforce sweep (g)",
    "downforce_target_actual_lateral_acceleration_m_per_s2": "Maximum lateral acceleration using the skidpad target downforce (m/s^2)",
    "downforce_target_actual_lateral_acceleration_g": "Maximum lateral acceleration using the skidpad target downforce (g)",
}

import matplotlib.pyplot as plt
import numpy as np


def main(parameters):
    sprung_mass = parameters["ms"]
    unsprung_mass = parameters["mu"]
    tire_friction = parameters["wl_mu_y"]
    target_downforce = parameters["skidpad_target_downforce_N"]
    target_lap_time = parameters["skidpad_target_lap_time_s"]
    if sprung_mass <= 0 or unsprung_mass <= 0 or tire_friction <= 0:
        raise ValueError("ms, mu, and wl_mu_y must be greater than zero")

    mass = sprung_mass + 4 * unsprung_mass
    gravity = 9.81
    downforce = np.linspace(0, 2500, 200)
    lateral_acceleration_g = tire_friction * (mass * gravity + downforce) / (mass * gravity)
    target_lateral_acceleration = tire_friction * (mass * gravity + target_downforce) / mass
    target_lateral_acceleration_g = target_lateral_acceleration / gravity

    figure, axis = plt.subplots(figsize=(8, 5))
    axis.plot(downforce, lateral_acceleration_g, linewidth=2, label="Maximum Lateral Acceleration")
    axis.scatter([0], [tire_friction], color="red", zorder=5, label=f"No Aero = {tire_friction:.2f} g")
    axis.scatter(
        [target_downforce],
        [target_lateral_acceleration_g],
        color="darkorange",
        marker="*",
        s=150,
        zorder=6,
        label=f"Skidpad target ({target_lap_time:.2f} s)",
    )
    axis.annotate(
        f"{target_lap_time:.2f} s\n{target_downforce:.0f} N\n"
        f"{target_lateral_acceleration:.2f} m/s² ({target_lateral_acceleration_g:.2f} g)",
        (target_downforce, target_lateral_acceleration_g),
        xytext=(8, 10),
        textcoords="offset points",
        color="darkorange",
    )
    x_min = min(0.0, target_downforce)
    x_max = max(2500.0, target_downforce)
    x_padding = max((x_max - x_min) * 0.05, 1.0)
    axis.set_xlim(x_min - x_padding, x_max + x_padding)
    axis.set_xlabel("Downforce (N)")
    axis.set_ylabel("Lateral Acceleration (g)")
    axis.set_title("Lateral Acceleration vs Downforce")
    axis.grid(True)
    axis.legend()
    figure.tight_layout()
    print(f"Skidpad target lap time: {target_lap_time:.2f} s")
    print(f"Skidpad target downforce: {target_downforce:.2f} N")
    print(
        "Actual maximum lateral acceleration at target downforce: "
        f"{target_lateral_acceleration:.3f} m/s^2 "
        f"({target_lateral_acceleration_g:.3f} g)"
    )
    return figure, {
        "downforce_target_max_lateral_acceleration_g": float(lateral_acceleration_g[-1]),
        "downforce_target_actual_lateral_acceleration_m_per_s2": float(
            target_lateral_acceleration
        ),
        "downforce_target_actual_lateral_acceleration_g": float(
            target_lateral_acceleration_g
        ),
    }
