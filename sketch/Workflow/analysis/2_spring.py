"""Find the tender spring rate that reduces heave stiffness to its target."""

TITLE = "2_spring"
DESCRIPTION = "Solve the tender-to-main spring stiffness ratio for a target series stiffness."
PLUGIN_ID = "two_spring"
PARAMETERS = {
    "Ks_pitch_N_per_m": "float",
    "Ks_scale_target_frequency": "float",
}
HIDDEN_PARAMETERS = {"Ks_pitch_N_per_m", "Ks_scale_target_frequency"}
OUTPUTS = {
    "K_heave_main_N_per_m": "Main pitch/heave spring stiffness passed to the tender analysis (N/m)",
    "K_tender_required_N_per_m": "Tender spring stiffness required in series with the main heave spring (N/m)",
    "tender_to_heave_stiffness_ratio": "Required tender stiffness divided by main heave stiffness",
    "K_series_target_N_per_m": "Target equivalent stiffness of the main and tender springs in series (N/m)",
}

import matplotlib.pyplot as plt
import numpy as np


def main(parameters):
    main_heave_stiffness = parameters["Ks_pitch_N_per_m"]
    target_stiffness_scale = parameters["Ks_scale_target_frequency"]
    if main_heave_stiffness <= 0:
        raise ValueError("Ks_pitch_N_per_m must be greater than zero")
    if not 0 < target_stiffness_scale < 1:
        raise ValueError(
            "Ks_scale_target_frequency must be between 0 and 1 for a finite positive "
            "tender spring in series with the main spring."
        )

    target_series_stiffness = main_heave_stiffness * target_stiffness_scale
    tender_stiffness = (
        target_series_stiffness * main_heave_stiffness
        / (main_heave_stiffness - target_series_stiffness)
    )
    tender_to_heave_ratio = tender_stiffness / main_heave_stiffness

    ratio_max = max(4.0, tender_to_heave_ratio * 1.1)
    tender_ratio = np.linspace(0.01, ratio_max, 1000)
    equivalent_ratio = tender_ratio / (1 + tender_ratio)
    equivalent_stiffness = equivalent_ratio * main_heave_stiffness

    figure, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].plot(tender_ratio * main_heave_stiffness / 1000, equivalent_stiffness / 1000)
    axes[0].scatter(
        [tender_stiffness / 1000],
        [target_series_stiffness / 1000],
        color="tab:red",
        zorder=5,
        label="Target stiffness",
    )
    axes[0].annotate(
        f"K_tender/K_heave = {tender_to_heave_ratio:.3f}\n"
        f"K_series = {target_series_stiffness / 1000:.2f} kN/m",
        (tender_stiffness / 1000, target_series_stiffness / 1000),
        xytext=(8, 8),
        textcoords="offset points",
    )
    axes[0].set_xlabel("Tender spring stiffness (kN/m)")
    axes[0].set_ylabel("Equivalent series stiffness (kN/m)")
    axes[0].set_title("Series Spring Equivalent Stiffness")
    axes[0].grid(True)
    axes[0].legend()

    axes[1].plot(tender_ratio * 100, equivalent_ratio * 100)
    axes[1].scatter(
        [tender_to_heave_ratio * 100],
        [target_stiffness_scale * 100],
        color="tab:red",
        zorder=5,
        label="Target stiffness ratio",
    )
    axes[1].axhline(target_stiffness_scale * 100, color="tab:red", linestyle="--", alpha=0.6)
    axes[1].set_xlabel("Tender stiffness (% of main heave stiffness)")
    axes[1].set_ylabel("Equivalent stiffness (% of main heave stiffness)")
    axes[1].set_title("Equivalent Stiffness Ratio")
    axes[1].grid(True)
    axes[1].legend()
    figure.tight_layout()

    print(f"Main heave stiffness: {main_heave_stiffness:.2f} N/m")
    print(f"Target series stiffness: {target_series_stiffness:.2f} N/m")
    print(f"Required tender stiffness: {tender_stiffness:.2f} N/m")
    print(f"Tender/main stiffness ratio: {tender_to_heave_ratio:.6f}×")
    return figure, {
        "K_heave_main_N_per_m": float(main_heave_stiffness),
        "K_tender_required_N_per_m": float(tender_stiffness),
        "tender_to_heave_stiffness_ratio": float(tender_to_heave_ratio),
        "K_series_target_N_per_m": float(target_series_stiffness),
    }
