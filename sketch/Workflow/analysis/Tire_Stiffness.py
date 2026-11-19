"""Estimate spring rates from the selected pitch and roll ride stiffnesses."""

TITLE = "Tire stiffness"
DESCRIPTION = "Estimate spring stiffness after accounting for tire compliance."
PLUGIN_ID = "tire_stiffness"
PARAMETERS = {
    "MR": "float",
    "Kt": "float",
    "frequency_roll_stiffness_used_N_per_m": "float",
    "frequency_pitch_stiffness_used_N_per_m": "float",
}
HIDDEN_PARAMETERS = {
    "frequency_roll_stiffness_used_N_per_m",
    "frequency_pitch_stiffness_used_N_per_m",
}
OUTPUTS = {
    "Ks": "Spring stiffness supplied to Time_sensitivity, Analytical_Numerical_Simulation and ode_spring (N/m)",
    "Ks_roll_N_per_m": "Spring stiffness for selected roll stiffness (N/m)",
    "Ks_pitch_N_per_m": "Spring stiffness for selected pitch stiffness (N/m)",
}

import matplotlib.pyplot as plt
import numpy as np


def ride_rate(motion_ratio, tire_stiffness, spring_stiffness):
    wheel_rate = spring_stiffness * motion_ratio**2
    return wheel_rate * tire_stiffness / (wheel_rate + tire_stiffness)


def calc_spring_rate(motion_ratio, target_ride_rate, tire_stiffness):
    if target_ride_rate >= tire_stiffness:
        raise ValueError("Target ride stiffness must be less than tire stiffness")
    wheel_rate = target_ride_rate * tire_stiffness / (tire_stiffness - target_ride_rate)
    return wheel_rate / motion_ratio**2


def main(parameters):
    motion_ratio = parameters["MR"]
    tire_stiffness = parameters["Kt"]
    roll_stiffness = parameters["frequency_roll_stiffness_used_N_per_m"]
    pitch_stiffness = parameters["frequency_pitch_stiffness_used_N_per_m"]
    if motion_ratio <= 0 or tire_stiffness <= 0:
        raise ValueError("MR and Kt must be greater than zero")
    if roll_stiffness <= 0 or pitch_stiffness <= 0:
        raise ValueError("Selected roll and pitch stiffnesses must be greater than zero")

    spring_stiffness_range = np.linspace(20_000, 80_000, 2000)
    ride_rate_range = ride_rate(motion_ratio, tire_stiffness, spring_stiffness_range)
    target_ride_rate = (roll_stiffness + pitch_stiffness) / 4
    index = int(np.argmin(np.abs(ride_rate_range - target_ride_rate)))
    target_spring_stiffness = float(spring_stiffness_range[index])
    actual_target_ride_rate = float(ride_rate_range[index])
    roll_spring_stiffness = calc_spring_rate(motion_ratio, roll_stiffness, tire_stiffness * 2)
    pitch_spring_stiffness = calc_spring_rate(
        motion_ratio, pitch_stiffness, tire_stiffness * 2
    )

    figure, axis = plt.subplots(figsize=(8, 5))
    axis.plot(
        spring_stiffness_range / 1000,
        ride_rate_range / 1000,
        linewidth=2,
        label="Ride rate",
    )
    axis.plot(
        spring_stiffness_range / 1000,
        spring_stiffness_range / 1000,
        linewidth=1.5,
        label="Spring rate without tire compliance",
    )
    axis.scatter(
        target_spring_stiffness / 1000,
        actual_target_ride_rate / 1000,
        color="red",
        s=70,
        zorder=5,
        label="Selected target",
    )
    axis.axvline(
        target_spring_stiffness / 1000,
        color="red",
        linestyle="--",
        linewidth=1.2,
        label="Selected spring stiffness",
    )
    axis.annotate(
        f"Ks = {target_spring_stiffness / 1000:.2f} kN/m\n"
        f"Kr = {actual_target_ride_rate / 1000:.2f} kN/m\n"
        f"Ks roll = {roll_spring_stiffness / 1000:.2f} kN/m\n"
        f"Ks pitch = {pitch_spring_stiffness / 1000:.2f} kN/m",
        xy=(target_spring_stiffness / 1000, actual_target_ride_rate / 1000),
        xytext=(18, 14),
        textcoords="offset points",
        arrowprops={"arrowstyle": "->"},
    )
    axis.grid(True)
    axis.set_xlabel("Spring stiffness (kN/m)")
    axis.set_ylabel("Ride rate (kN/m)")
    axis.set_title("Spring stiffness vs. ride rate")
    axis.legend()
    figure.tight_layout()

    print(f"Target spring stiffness Ks: {target_spring_stiffness:.2f} N/m")
    print(f"Spring stiffness for roll target: {roll_spring_stiffness:.2f} N/m")
    print(f"Spring stiffness for pitch target: {pitch_spring_stiffness:.2f} N/m")
    return figure, {
        "Ks": target_spring_stiffness,
        "Ks_roll_N_per_m": float(roll_spring_stiffness),
        "Ks_pitch_N_per_m": float(pitch_spring_stiffness),
    }
