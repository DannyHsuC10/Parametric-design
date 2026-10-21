"""Ideal inner/outer wheel steering geometry, retaining the source rate definition."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis.cornering.models import ackermann_angles, sweep
from analysis_result import AnalysisResult

TITLE = "ideal_ackemann"
DESCRIPTION = "Ideal Ackermann wheel angles and (inner - outer) / inner angle percentage."
PLUGIN_ID = "ideal_ackemann"
ACKERMANN_RADIUS_MIN_M = 3.0
ACKERMANN_RADIUS_MAX_M = 30.0
NUM_POINTS_ACKERMANN = 51
PARAMETERS = {"L": "float", "t": "float"}
HIDDEN_PARAMETERS = {"L"}
OUTPUTS = {"ackermann_inner_max_deg": "Maximum inner wheel steering angle (deg)",
           "ackermann_outer_max_deg": "Maximum outer wheel steering angle (deg)",
           "ackermann_angle_difference_ratio_max_percent": "Maximum (inner - outer) / inner angle ratio (%)"}


def main(parameters):
    radius = sweep(ACKERMANN_RADIUS_MIN_M, ACKERMANN_RADIUS_MAX_M,
                   NUM_POINTS_ACKERMANN, "Ackermann radius sweep")
    inner, outer = ackermann_angles(radius, parameters["L"], parameters["t"])
    inner_deg, outer_deg = np.rad2deg(inner), np.rad2deg(outer)
    rate = (inner_deg - outer_deg) / inner_deg * 100
    figure, axes = plt.subplots(2, 1, figsize=(8, 8), sharex=True)
    axes[0].plot(radius, inner_deg, "r-", linewidth=2, label="Inner wheel")
    axes[0].plot(radius, outer_deg, "b-", linewidth=2, label="Outer wheel")
    axes[0].set(ylabel="Steering angle (deg)", title="Ideal Ackermann steering geometry")
    axes[0].legend()
    axes[1].plot(radius, rate, linewidth=2)
    axes[1].set(xlabel="Turning radius R (m)", ylabel="Angle difference / inner (%)",
                title="Inner / outer steering angle difference ratio")
    for axis in axes:
        axis.grid(True)
    figure.tight_layout()
    outputs = {"ackermann_inner_max_deg": float(inner_deg.max()),
               "ackermann_outer_max_deg": float(outer_deg.max()),
               "ackermann_angle_difference_ratio_max_percent": float(rate.max())}
    print(f"Maximum inner / outer angles: {inner_deg.max():.3f} / {outer_deg.max():.3f} deg")
    return AnalysisResult(figure, outputs,
                          tables={"ackermann_geometry.csv": pd.DataFrame({"radius_m": radius,
                                  "inner_angle_deg": inner_deg, "outer_angle_deg": outer_deg,
                                  "angle_difference_ratio_percent": rate})},
                          figure_titles={"plot.png": "理想 Ackermann 內外輪角與角差比例"})
