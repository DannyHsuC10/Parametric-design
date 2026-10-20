"""Estimate tire ring-mode natural frequencies."""

TITLE = "Tire_Ring_Mode"
DESCRIPTION = "Calculate and plot the natural frequencies of tire ring modes."
PLUGIN_ID = "tire_ring_mode"
PARAMETERS = {
    "R_tire": "float",
    "youngs_modulus_tire": "float",
    "volume_tire": "float",
    "m_tire": "float",
    "cross_section_area_tire": "float",
    "second_moment_area_tire": "float",
}
OUTPUTS = {
    "tire_ring_mode_2_Hz": "Tire ring mode 2 frequency (Hz)",
    "tire_ring_mode_3_Hz": "Tire ring mode 3 frequency (Hz)",
    "tire_ring_mode_4_Hz": "Tire ring mode 4 frequency (Hz)",
    "tire_ring_mode_5_Hz": "Tire ring mode 5 frequency (Hz)",
}

import matplotlib.pyplot as plt
import numpy as np


def main(parameters):
    R_tire = parameters["R_tire"]  # Tire radius (m)
    youngs_modulus_tire = parameters["youngs_modulus_tire"]  # Pa
    volume_tire = parameters["volume_tire"]  # m^3
    m_tire = parameters["m_tire"]  # kg
    cross_section_area_tire = parameters["cross_section_area_tire"]  # m^2
    second_moment_area_tire = parameters["second_moment_area_tire"]  # m^4
    mode_max = 5

    if min(
        R_tire,
        youngs_modulus_tire,
        volume_tire,
        m_tire,
        cross_section_area_tire,
        second_moment_area_tire,
    ) <= 0:
        raise ValueError("All tire parameters must be greater than zero")

    density_tire = m_tire / volume_tire
    modes = np.arange(1, mode_max + 1)
    frequency = np.zeros(mode_max)
    for mode in range(2, mode_max + 1):
        omega = np.sqrt(
            (youngs_modulus_tire * second_moment_area_tire)
            / (density_tire * cross_section_area_tire * R_tire**4)
        ) * (mode**2 * (mode**2 - 1))
        frequency[mode - 1] = omega / (2 * np.pi)

    figure, axis = plt.subplots(figsize=(8, 5))
    axis.plot(modes, frequency, "-o", linewidth=2, markersize=6)
    for mode, mode_frequency in zip(modes, frequency):
        axis.annotate(
            str(mode),
            (mode, mode_frequency),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
        )
    axis.grid(True)
    axis.set_xlabel("Mode Number")
    axis.set_ylabel("Frequency (Hz)")
    axis.set_title("Tire Ring Mode Frequencies")
    figure.tight_layout()

    for mode in range(2, mode_max + 1):
        print(f"Mode {mode}: {frequency[mode - 1]:.2f} Hz")
    outputs = {
        f"tire_ring_mode_{mode}_Hz": float(frequency[mode - 1])
        for mode in range(2, mode_max + 1)
    }
    return figure, outputs
