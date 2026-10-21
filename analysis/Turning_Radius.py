"""Steering-angle sweep using the shared wheelbase from the mass source."""

import matplotlib.pyplot as plt
import pandas as pd

from analysis.cornering.models import sweep, turning_radius
from analysis_result import AnalysisResult

TITLE = "Turning_Radius"
DESCRIPTION = "Theoretical rear-axle-center turning radius: R = L / tan(theta)."
PLUGIN_ID = "turning_radius"
TURNING_ANGLE_MIN_DEG = 10.0
TURNING_ANGLE_MAX_DEG = 60.0
NUM_POINTS_TURNING_RADIUS = 500
PARAMETER_DEFAULTS = {"vehicle_max_steering_angle_deg": 45.0}
PARAMETERS = {"L": "float", "vehicle_max_steering_angle_deg": "float"}
OUTPUTS = {"turning_radius_min_m": "Minimum rear axle center turning radius over the steering sweep (m)",
           "turning_radius_max_m": "Maximum rear axle center turning radius over the steering sweep (m)",
           "turning_radius_at_max_steering_m": "Rear axle center turning radius at the vehicle maximum steering angle (m)"}


def main(parameters):
    values = PARAMETER_DEFAULTS | parameters
    selected_angle = values["vehicle_max_steering_angle_deg"]
    selected_radius = float(turning_radius(selected_angle, values["L"]))
    angle = sweep(TURNING_ANGLE_MIN_DEG, TURNING_ANGLE_MAX_DEG,
                  NUM_POINTS_TURNING_RADIUS, "Steering sweep")
    radius = turning_radius(angle, values["L"])
    figure, axis = plt.subplots(figsize=(8, 5))
    axis.plot(angle, radius, linewidth=2)
    axis.scatter([selected_angle], [selected_radius], s=35, color="crimson", zorder=5)
    right_side = selected_angle >= (TURNING_ANGLE_MIN_DEG + TURNING_ANGLE_MAX_DEG) / 2
    axis.annotate(
        f"Max steering: {selected_angle:.2f}°\nR = {selected_radius:.3f} m",
        (selected_angle, selected_radius), textcoords="offset points",
        xytext=(-12 if right_side else 12, -38 if selected_radius > radius.max() * 0.8 else 22),
        ha="right" if right_side else "left", fontsize=10, color="crimson",
        arrowprops={"arrowstyle": "-", "color": "crimson", "linewidth": 0.8},
    )
    axis.set(xlabel="Steering Angle (deg)", ylabel="Turning Radius R (m)",
             title=r"Theoretical Turning Radius: $R=L/\tan(\theta)$",
             xlim=(0, max(TURNING_ANGLE_MAX_DEG, selected_angle) + 3),
             ylim=(0, max(radius.max(), selected_radius) * 1.08))
    axis.grid(True)
    figure.tight_layout()
    outputs = {"turning_radius_min_m": float(radius.min()), "turning_radius_max_m": float(radius.max()),
               "turning_radius_at_max_steering_m": selected_radius}
    print(f"Turning radius range: {radius.min():.3f}–{radius.max():.3f} m")
    print(f"Vehicle maximum steering: {selected_angle:.2f} deg; turning radius: {selected_radius:.3f} m")
    return AnalysisResult(figure, outputs,
                          tables={"turning_radius.csv": pd.DataFrame({"steering_angle_deg": angle,
                                                                     "radius_m": radius}),
                                  "vehicle_turning_limit.csv": pd.DataFrame({
                                      "max_steering_angle_deg": [selected_angle],
                                      "turning_radius_m": [selected_radius]})},
                          figure_titles={"plot.png": "轉向角與理論迴轉半徑"})
