"""Evaluate equivalent stiffness as chassis stiffness increases."""

TITLE = "Overall Rigidity"
DESCRIPTION = "Show how chassis stiffness affects overall equivalent stiffness."
PLUGIN_ID = "overall_rigidity"
PARAMETERS = {
    "Ks": "float",
    "Kt": "float",
}
HIDDEN_PARAMETERS = {"Ks"}
OUTPUTS = {
    "overall_rigidity_saturation_N_per_m": "Equivalent stiffness limit as chassis stiffness approaches infinity (N/m)",
}

import matplotlib.pyplot as plt
import numpy as np


def main(parameters):
    spring_stiffness = parameters["Ks"]
    tire_stiffness = parameters["Kt"]
    if spring_stiffness <= 0 or tire_stiffness <= 0:
        raise ValueError("Ks and Kt must be greater than zero")

    ratio = np.arange(1, 21)
    chassis_stiffness = ratio * spring_stiffness
    equivalent_stiffness = 1.0 / (
        1.0 / tire_stiffness + 1.0 / spring_stiffness + 1.0 / chassis_stiffness
    )
    saturation_stiffness = 1.0 / (1.0 / tire_stiffness + 1.0 / spring_stiffness)

    figure, axis = plt.subplots(figsize=(8, 5))
    highlight_ratios = [3, 5, 10]
    colors = {3: "green", 5: "orange", 10: "red"}
    for highlight_ratio in highlight_ratios:
        index = np.where(ratio == highlight_ratio)[0][0]
        value = equivalent_stiffness[index]
        axis.axvline(
            highlight_ratio,
            linestyle="--",
            color=colors[highlight_ratio],
            linewidth=2,
            label=f"{highlight_ratio}× Rule",
        )
        axis.scatter(highlight_ratio, value, color=colors[highlight_ratio], s=70, zorder=5)
        axis.annotate(
            f"{value:,.0f} N/m",
            xy=(highlight_ratio, value),
            xytext=(8, 10),
            textcoords="offset points",
            color=colors[highlight_ratio],
        )

    axis.plot(
        ratio,
        equivalent_stiffness,
        "o-",
        linewidth=2,
        markersize=6,
        label="Equivalent Stiffness",
    )
    axis.axhline(
        saturation_stiffness,
        linestyle="--",
        color="black",
        linewidth=2,
        label="Saturation Limit",
    )
    axis.grid(True)
    axis.set_xlabel("Chassis Stiffness / Suspension Stiffness Ratio ($K_c/K_s$)")
    axis.set_ylabel("Equivalent Stiffness $K_{eq}$ (N/m)")
    axis.set_title("Effect of Chassis Stiffness on Overall Stiffness")
    axis.legend()
    figure.tight_layout()

    print(f"Equivalent stiffness saturation limit: {saturation_stiffness:,.1f} N/m")
    return figure, {"overall_rigidity_saturation_N_per_m": float(saturation_stiffness)}
