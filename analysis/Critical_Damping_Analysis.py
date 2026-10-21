"""Natural frequency and critical damping across a spring-stiffness range."""

import matplotlib.pyplot as plt
import numpy as np

from oscillation_models import require_positive

TITLE = "Critical_Damping_Analysis"
PLUGIN_ID = "critical_damping_analysis"
DESCRIPTION = "Natural frequency and reference critical damping versus stiffness, marking Tire stiffness Ks."
PARAMETERS = {"ms": "float", "Ks": "float"}
HIDDEN_PARAMETERS = {"Ks"}
OUTPUTS = {
    "critical_damping_mass_used_kg": "Quarter sprung mass (kg)",
    "critical_damping_stiffness_used_N_per_m": "Marked spring stiffness Ks (N/m)",
    "critical_damping_at_Ks_Ns_per_m": "SDOF reference critical damping at Ks (N s/m)",
    "critical_damping_frequency_at_Ks_Hz": "SDOF undamped natural frequency at Ks (Hz)",
}

STIFFNESS_MIN_N_PER_M = 10_000.0
STIFFNESS_MAX_N_PER_M = 300_000.0
STIFFNESS_SAMPLES = 1000


def main(parameters):
    require_positive(parameters, "ms", "Ks")
    mass, selected = parameters["ms"] / 4, parameters["Ks"]
    stiffness = np.linspace(STIFFNESS_MIN_N_PER_M, STIFFNESS_MAX_N_PER_M, STIFFNESS_SAMPLES)
    frequency = np.sqrt(stiffness / mass) / (2 * np.pi)
    critical = 2 * np.sqrt(stiffness * mass)
    selected_frequency = np.sqrt(selected / mass) / (2 * np.pi)
    selected_critical = 2 * np.sqrt(selected * mass)
    figure, axes = plt.subplots(2, 1, figsize=(9, 8), sharex=True)
    for axis, values, marker, ylabel in zip(
        axes, (frequency, critical), (selected_frequency, selected_critical),
        ("Natural frequency (Hz)", "Critical damping (N s/m)"),
    ):
        axis.plot(stiffness / 1000, values)
        axis.scatter([selected / 1000], [marker], color="tab:red", zorder=5, label="Tire stiffness Ks")
        axis.axvline(selected / 1000, color="tab:red", linestyle="--", alpha=0.6)
        axis.set_ylabel(ylabel)
        axis.grid(True)
        axis.legend()
    axes[0].set_title(f"Frequency and critical damping | quarter sprung mass = {mass:g} kg")
    axes[1].set_xlabel("Spring stiffness (kN/m)")
    figure.tight_layout()
    print(f"Quarter sprung mass: {mass:g} kg; Tire stiffness Ks: {selected:.6f} N/m")
    print(f"Reference critical damping at Ks: {selected_critical:.6f} N s/m")
    return figure, {
        "critical_damping_mass_used_kg": float(mass),
        "critical_damping_stiffness_used_N_per_m": float(selected),
        "critical_damping_at_Ks_Ns_per_m": float(selected_critical),
        "critical_damping_frequency_at_Ks_Hz": float(selected_frequency),
    }
