"""Estimate pitch and roll stiffness requirements at selected vehicle angles."""

TITLE = "Aero stiffness"
DESCRIPTION = "Calculate pitch and roll stiffness from acceleration, CG height, and vehicle dimensions."
PLUGIN_ID = "aero_stiffness"
PARAMETERS = {
    "ms": "float",
    "ax": "float",
    "ay": "float",
    "h_cog": "float",
    "L": "float",
    "t": "float",
    "target_pitch_angle_deg": "float",
    "target_roll_angle_deg": "float",
}
OUTPUTS = {
    "aero_pitch_stiffness_target_N_per_m": "Pitch stiffness at the selected pitch angle (N/m)",
    "aero_roll_stiffness_target_N_per_m": "Roll stiffness at the selected roll angle (N/m)",
    "aero_pitch_displacement_target_m": "Pitch displacement at the selected angle (m)",
    "aero_roll_displacement_target_m": "Roll displacement at the selected angle (m)",
}

import numpy as np
import matplotlib.pyplot as plt


def main(parameters):
    mass = parameters["ms"]
    acceleration_x_g = parameters["ax"]
    acceleration_y_g = parameters["ay"]
    center_of_gravity_height = parameters["h_cog"]
    wheelbase = parameters["L"]
    track_width = parameters["t"]
    target_pitch_angle = parameters["target_pitch_angle_deg"]
    target_roll_angle = parameters["target_roll_angle_deg"]

    if mass <= 0:
        raise ValueError("ms must be greater than zero")
    if center_of_gravity_height <= 0:
        raise ValueError("h_cog must be greater than zero")
    if wheelbase <= 0 or track_width <= 0:
        raise ValueError("L and t must be greater than zero")
    if not 0.1 <= target_pitch_angle <= 3.0:
        raise ValueError("target_pitch_angle_deg must be between 0.1 and 3.0 degrees")
    if not 0.1 <= target_roll_angle <= 3.0:
        raise ValueError("target_roll_angle_deg must be between 0.1 and 3.0 degrees")

    gravity = 9.81
    angle_deg = np.arange(0.1, 3.01, 0.1)
    angle_rad = np.deg2rad(angle_deg)

    pitch_displacement = (wheelbase / 2) * angle_rad
    pitch_force = (
        mass * acceleration_x_g * gravity * center_of_gravity_height
    ) / (wheelbase / 2)
    pitch_stiffness = pitch_force / (2 * pitch_displacement)

    roll_displacement = (track_width / 2) * angle_rad
    roll_force = (mass * acceleration_y_g * gravity * center_of_gravity_height) / (track_width / 2)
    roll_stiffness = roll_force / (2 * roll_displacement)

    pitch_index = int(np.argmin(np.abs(angle_deg - target_pitch_angle)))
    roll_index = int(np.argmin(np.abs(angle_deg - target_roll_angle)))
    pitch_stiffness_target = float(pitch_stiffness[pitch_index])
    roll_stiffness_target = float(roll_stiffness[roll_index])
    pitch_displacement_target = float(pitch_displacement[pitch_index])
    roll_displacement_target = float(roll_displacement[roll_index])

    print(
        f"Pitch stiffness @ {angle_deg[pitch_index]:.1f}° = "
        f"{pitch_stiffness_target:.1f} N/m"
    )
    print(
        f"Roll stiffness @ {angle_deg[roll_index]:.1f}° = "
        f"{roll_stiffness_target:.1f} N/m"
    )

    figure, axis = plt.subplots(figsize=(8, 5))
    axis.plot(pitch_stiffness, angle_deg, linewidth=2, label="Pitch")
    axis.plot(roll_stiffness, angle_deg, linewidth=2, label="Roll")
    axis.scatter(pitch_stiffness_target, angle_deg[pitch_index], color="red", zorder=3)
    axis.scatter(roll_stiffness_target, angle_deg[roll_index], color="blue", zorder=3)
    axis.annotate(
        f"{pitch_stiffness_target:,.0f} N/m\n@ {angle_deg[pitch_index]:.1f}°",
        (pitch_stiffness_target, angle_deg[pitch_index]),
        xytext=(10, 10),
        textcoords="offset points",
        color="red",
    )
    axis.annotate(
        f"{roll_stiffness_target:,.0f} N/m\n@ {angle_deg[roll_index]:.1f}°",
        (roll_stiffness_target, angle_deg[roll_index]),
        xytext=(10, -32),
        textcoords="offset points",
        color="blue",
    )
    axis.grid(True)
    axis.set_xlabel("Required stiffness (N/m)")
    axis.set_ylabel("Allowable angle (deg)")
    axis.set_title("Pitch and roll stiffness requirements")
    axis.legend()
    figure.tight_layout()

    outputs = {
        "aero_pitch_stiffness_target_N_per_m": pitch_stiffness_target,
        "aero_roll_stiffness_target_N_per_m": roll_stiffness_target,
        "aero_pitch_displacement_target_m": pitch_displacement_target,
        "aero_roll_displacement_target_m": roll_displacement_target,
    }
    return figure, outputs
