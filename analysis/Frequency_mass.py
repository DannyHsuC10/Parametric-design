"""Quarter-car natural frequencies across unsprung mass ratios."""

TITLE = "Frequency vs mass"
DESCRIPTION = "Calculate sprung and wheel-hop modes across unsprung mass ratio."
PLUGIN_ID = "frequency_mass"
PARAMETERS = {
    "ms": "float",
    "mu": "float",
    "Ks_roll_N_per_m": "float",
    "Ks_pitch_N_per_m": "float",
    "Kt": "float",
    "MR": "float",
    "N": "float",
}
HIDDEN_PARAMETERS = {"Ks_roll_N_per_m", "Ks_pitch_N_per_m"}
OUTPUTS = {
    "m_total_vehicle_kg": "Calculated total vehicle mass (ms + 4 × mu) (kg)",
    "unsprung_mass_ratio_target_percent": "Target unsprung mass ratio (%)",
    "frequency_sprung_target_Hz": "Sprung-mass mode at target ratio (Hz)",
    "frequency_unsprung_target_Hz": "Wheel-hop mode at target ratio (Hz)",
    "target_natural_frequency_Hz": "Target natural frequency calculated as unsprung frequency divided by N (Hz)",
    "Ks_required_target_frequency_N_per_m": "Pitch/heave spring stiffness required to reach the target natural frequency while holding roll stiffness fixed (N/m)",
    "Ks_scale_target_frequency": "Multiplier applied to Ks_pitch_N_per_m (K_pitch/K_heave), with roll stiffness fixed",
}

import matplotlib.pyplot as plt
import numpy as np


def main(parameters):
    target_unsprung_mass = parameters["mu"]
    sprung_mass_vehicle = parameters["ms"]
    m = target_unsprung_mass * 4 + sprung_mass_vehicle
    total_mass = m / 4
    spring_stiffness = parameters["Ks_pitch_N_per_m"]
    roll_spring_stiffness = parameters["Ks_roll_N_per_m"]
    tire_stiffness = parameters["Kt"]
    motion_ratio = parameters["MR"]
    frequency_divisor = parameters["N"]
    if sprung_mass_vehicle <= 0 or target_unsprung_mass <= 0:
        raise ValueError("ms and mu must be greater than zero")
    if target_unsprung_mass >= total_mass:
        raise ValueError("mu must be less than the quarter-car mass ((4 * mu + ms) / 4)")
    if spring_stiffness <= 0 or roll_spring_stiffness <= 0 or tire_stiffness <= 0 or motion_ratio <= 0:
        raise ValueError("Ks_pitch_N_per_m, Ks_roll_N_per_m, Kt, and MR must be greater than zero")
    if frequency_divisor <= 0:
        raise ValueError("N must be greater than zero")

    equivalent_spring_stiffness = (roll_spring_stiffness + spring_stiffness) / 4
    wheel_rate = equivalent_spring_stiffness * motion_ratio**2
    ride_rate = wheel_rate * tire_stiffness / (wheel_rate + tire_stiffness)
    ratio = np.linspace(0.05, 0.50, 500)
    unsprung_mass = total_mass * ratio
    sprung_mass = total_mass - unsprung_mass
    sprung_frequency = np.sqrt(ride_rate / sprung_mass) / (2 * np.pi)
    unsprung_frequency = np.sqrt((tire_stiffness + wheel_rate) / unsprung_mass) / (2 * np.pi)

    target_ratio = target_unsprung_mass / total_mass
    target_frequency_sprung = float(np.sqrt(ride_rate / (total_mass - target_unsprung_mass)) / (2 * np.pi))
    target_frequency_unsprung = float(
        np.sqrt((tire_stiffness + wheel_rate) / target_unsprung_mass) / (2 * np.pi)
    )
    target_natural_frequency = target_frequency_unsprung / frequency_divisor

    def required_spring_stiffness(target_frequency):
        required_ride_rate = (
            (2 * np.pi * target_frequency) ** 2
            * (total_mass - target_unsprung_mass)
        )
        if required_ride_rate >= tire_stiffness:
            raise ValueError(
                f"Target frequency {target_frequency:.3f} Hz cannot be reached: "
                "the required ride rate must be lower than tire stiffness Kt."
            )
        required_wheel_rate = (
            tire_stiffness * required_ride_rate
            / (tire_stiffness - required_ride_rate)
        )
        required_equivalent_spring_stiffness = required_wheel_rate / motion_ratio**2
        return 4 * required_equivalent_spring_stiffness - roll_spring_stiffness

    required_target_spring_stiffness = required_spring_stiffness(target_natural_frequency)
    if required_target_spring_stiffness <= 0:
        raise ValueError(
            "Target frequency is below the minimum set by the fixed roll stiffness; "
            "no positive heave spring stiffness can meet it."
        )
    target_stiffness_scale = required_target_spring_stiffness / spring_stiffness

    figure, axis = plt.subplots(figsize=(8, 5))
    axis.plot(ratio * 100, sprung_frequency, linewidth=2, label="Sprung mass mode")
    axis.plot(ratio * 100, unsprung_frequency, linewidth=2, label="Unsprung mass mode")
    axis.axvline(target_ratio * 100, color="gray", linestyle="--", label="Target ratio")
    axis.scatter(target_ratio * 100, target_frequency_sprung, color="tab:red", zorder=5)
    axis.scatter(target_ratio * 100, target_frequency_unsprung, color="tab:blue", zorder=5)
    axis.annotate(
        f"{target_frequency_sprung:.2f} Hz",
        (target_ratio * 100, target_frequency_sprung),
        xytext=(8, 8),
        textcoords="offset points",
        color="tab:red",
    )
    axis.annotate(
        f"{target_frequency_unsprung:.2f} Hz",
        (target_ratio * 100, target_frequency_unsprung),
        xytext=(8, -18),
        textcoords="offset points",
        color="tab:blue",
    )
    axis.grid(True)
    axis.set_xlabel("Unsprung mass ratio (%)")
    axis.set_ylabel("Natural frequency (Hz)")
    axis.set_title("Natural frequency vs. unsprung mass ratio")
    axis.legend()
    figure.tight_layout()

    outputs = {
        "m_total_vehicle_kg": m,
        "unsprung_mass_ratio_target_percent": target_ratio * 100,
        "frequency_sprung_target_Hz": target_frequency_sprung,
        "frequency_unsprung_target_Hz": target_frequency_unsprung,
        "target_natural_frequency_Hz": float(target_natural_frequency),
        "Ks_required_target_frequency_N_per_m": float(required_target_spring_stiffness),
        "Ks_scale_target_frequency": float(target_stiffness_scale),
    }
    print(f"Calculated vehicle mass (m = 4 × mu + ms): {m:.2f} kg")
    print(f"Target unsprung mass ratio: {target_ratio:.1%}")
    print(f"Sprung frequency: {target_frequency_sprung:.2f} Hz")
    print(f"Wheel-hop frequency: {target_frequency_unsprung:.2f} Hz")
    print(
        f"Target natural frequency (unsprung frequency / N = "
        f"{target_frequency_unsprung:.2f} / {frequency_divisor}): "
        f"{target_natural_frequency:.2f} Hz"
    )
    print(
        f"Ks for target frequency ({target_natural_frequency:.2f} Hz): "
        f"{required_target_spring_stiffness:.2f} N/m "
        f"({target_stiffness_scale:.4f} × current Ks_pitch_N_per_m / K_heave)"
    )
    return figure, outputs
