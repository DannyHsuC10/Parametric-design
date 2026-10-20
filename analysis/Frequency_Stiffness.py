"""Natural frequency across spring stiffness for the selected vehicle setup."""

TITLE = "Frequency vs stiffness"
DESCRIPTION = "Calculate sprung-mass natural frequency across a stiffness range."
PLUGIN_ID = "frequency_stiffness"
PARAMETERS = {
    "ms": "float",
    "roll_stiffness_target_N_per_m": "float",
    "aero_roll_stiffness_target_N_per_m": "float",
    "pitch_stiffness_target_N_per_m": "float",
    "aero_pitch_stiffness_target_N_per_m": "float",
}
HIDDEN_PARAMETERS = {
    "roll_stiffness_target_N_per_m",
    "aero_roll_stiffness_target_N_per_m",
    "pitch_stiffness_target_N_per_m",
    "aero_pitch_stiffness_target_N_per_m",
}
OUTPUTS = {
    "frequency_roll_stiffness_used_N_per_m": "Selected roll stiffness used for frequency calculation (N/m)",
    "frequency_pitch_stiffness_used_N_per_m": "Selected pitch stiffness used for frequency calculation (N/m)",
    "frequency_roll_Hz": "Natural frequency at roll ride rate (Hz)",
    "frequency_pitch_Hz": "Natural frequency at pitch ride rate (Hz)",
}

import matplotlib.pyplot as plt
import numpy as np


def main(parameters):
    sprung_mass = parameters["ms"] / 2
    roll_stiffness = max(
        parameters["roll_stiffness_target_N_per_m"],
        parameters["aero_roll_stiffness_target_N_per_m"],
    )
    pitch_stiffness = max(
        parameters["pitch_stiffness_target_N_per_m"],
        parameters["aero_pitch_stiffness_target_N_per_m"],
    )
    if sprung_mass <= 0:
        raise ValueError("ms must be greater than zero")
    if roll_stiffness <= 0 or pitch_stiffness <= 0:
        raise ValueError("Selected pitch and roll stiffnesses must be greater than zero")

    stiffness = np.linspace(10_000, 100_000, 5000)
    frequency = np.sqrt(stiffness / sprung_mass) / (2 * np.pi)
    roll_frequency = float(np.sqrt(roll_stiffness / sprung_mass) / (2 * np.pi))
    pitch_frequency = float(np.sqrt(pitch_stiffness / sprung_mass) / (2 * np.pi))
    print(
        "Roll stiffness used: max("
        f"{parameters['roll_stiffness_target_N_per_m']:.2f}, "
        f"{parameters['aero_roll_stiffness_target_N_per_m']:.2f}) "
        f"= {roll_stiffness:.2f} N/m"
    )
    print(
        "Pitch stiffness used: max("
        f"{parameters['pitch_stiffness_target_N_per_m']:.2f}, "
        f"{parameters['aero_pitch_stiffness_target_N_per_m']:.2f}) "
        f"= {pitch_stiffness:.2f} N/m"
    )

    figure, axis = plt.subplots(figsize=(8, 5))
    axis.plot(stiffness / 1000, frequency, linewidth=2)
    for value, result, label, color in (
        (roll_stiffness, roll_frequency, "Roll", "tab:red"),
        (pitch_stiffness, pitch_frequency, "Pitch", "tab:blue"),
    ):
        axis.scatter(value / 1000, result, color=color, zorder=5, label=label)
        axis.annotate(
            f"{label}: {result:.2f} Hz",
            (value / 1000, result),
            xytext=(6, 8),
            textcoords="offset points",
            color=color,
        )
    axis.grid(True)
    axis.set_xlabel("Ride rate (kN/m)")
    axis.set_ylabel("Natural frequency (Hz)")
    axis.set_title("Natural frequency vs. ride rate")
    axis.legend()
    figure.tight_layout()

    return figure, {
        "frequency_roll_stiffness_used_N_per_m": roll_stiffness,
        "frequency_pitch_stiffness_used_N_per_m": pitch_stiffness,
        "frequency_roll_Hz": roll_frequency,
        "frequency_pitch_Hz": pitch_frequency,
    }
