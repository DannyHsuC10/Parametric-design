"""Suspension compression, stiffness, and vehicle-angle analysis."""

TITLE = "Compressed travel"
DESCRIPTION = "Estimate pitch/roll wheel stiffness and vehicle angles over suspension travel."
PLUGIN_ID = "compressed_travel"
PARAMETERS = {
    "ms": "float",
    "ax": "float",
    "ay": "float",
    "sus_travel": "float",
    "h_cog": "float",
    "L": "float",
    "t": "float",
}
OUTPUTS = {
    "pitch_stiffness_target_N_per_m": "Pitch stiffness at target suspension travel (N/m)",
    "roll_stiffness_target_N_per_m": "Roll stiffness at target suspension travel (N/m)",
    "pitch_angle_target_deg": "Pitch angle at target suspension travel (deg)",
    "roll_angle_target_deg": "Roll angle at target suspension travel (deg)",
}

import numpy as np
import matplotlib.pyplot as plt


def main(parameters):
    mass = parameters["ms"]
    acceleration_x_g = parameters["ax"]
    acceleration_y_g = parameters["ay"]
    target_travel = parameters["sus_travel"]
    center_of_gravity_height = parameters["h_cog"]
    wheelbase = parameters["L"]
    track_width = parameters["t"]

    if mass <= 0:
        raise ValueError("ms must be greater than zero")
    if wheelbase <= 0 or track_width <= 0:
        raise ValueError("L and t must be greater than zero")
    if target_travel <= 0:
        raise ValueError("sus_travel must be greater than zero")
    if target_travel > 0.05:
        raise ValueError("sus_travel must not exceed the 0.050 m analysis range")

    gravity = 9.81
    travel = np.arange(0.005, 0.0501, 0.005)

    longitudinal_load_transfer = (
        mass * acceleration_x_g * gravity * center_of_gravity_height / wheelbase
    )
    lateral_load_transfer = (
        mass * acceleration_y_g * gravity * center_of_gravity_height / track_width
    )

    pitch_stiffness = longitudinal_load_transfer / travel
    roll_stiffness = lateral_load_transfer / travel
    target_index = int(np.argmin(np.abs(travel - target_travel)))
    target_pitch_stiffness = float(pitch_stiffness[target_index])
    target_roll_stiffness = float(roll_stiffness[target_index])

    pitch_angle = np.rad2deg(np.arctan(2 * travel / wheelbase))
    roll_angle = np.rad2deg(np.arctan(2 * travel / track_width))
    target_pitch_angle = float(np.rad2deg(np.arctan(2 * target_travel / wheelbase)))
    target_roll_angle = float(np.rad2deg(np.arctan(2 * target_travel / track_width)))

    print(f"Pitch stiffness at target travel: {target_pitch_stiffness:.1f} N/m")
    print(f"Roll stiffness at target travel: {target_roll_stiffness:.1f} N/m")
    print(f"Pitch angle at target travel: {target_pitch_angle:.2f} deg")
    print(f"Roll angle at target travel: {target_roll_angle:.2f} deg")

    figure, (stiffness_axis, angle_axis) = plt.subplots(1, 2, figsize=(12, 5))

    stiffness_axis.plot(pitch_stiffness, travel, "-r", linewidth=2, label="Pitch")
    stiffness_axis.plot(roll_stiffness, travel, "-b", linewidth=2, label="Roll")
    stiffness_axis.axhline(target_travel, linestyle="--", color="black", label="Target travel")
    stiffness_axis.scatter(target_pitch_stiffness, travel[target_index], color="red", zorder=5)
    stiffness_axis.scatter(target_roll_stiffness, travel[target_index], color="blue", zorder=5)
    stiffness_axis.set_xlabel("Wheel rate (N/m)")
    stiffness_axis.set_ylabel("Suspension compression (m)")
    stiffness_axis.set_title("Required pitch / roll stiffness")
    stiffness_axis.grid(True)
    stiffness_axis.legend()

    travel_mm = travel * 1000
    angle_axis.plot(travel_mm, pitch_angle, "-r", linewidth=2, label="Pitch")
    angle_axis.plot(travel_mm, roll_angle, "-b", linewidth=2, label="Roll")
    angle_axis.scatter(target_travel * 1000, target_pitch_angle, color="red", zorder=5)
    angle_axis.scatter(target_travel * 1000, target_roll_angle, color="blue", zorder=5)
    angle_axis.set_xlabel("Suspension travel (mm)")
    angle_axis.set_ylabel("Vehicle angle (deg)")
    angle_axis.set_title("Travel vs. pitch / roll angle")
    angle_axis.grid(True)
    angle_axis.legend()

    figure.tight_layout()
    outputs = {
        "pitch_stiffness_target_N_per_m": target_pitch_stiffness,
        "roll_stiffness_target_N_per_m": target_roll_stiffness,
        "pitch_angle_target_deg": target_pitch_angle,
        "roll_angle_target_deg": target_roll_angle,
    }
    return figure, outputs
