"""Cornering-speed limit over a radius sweep, using the shared tire friction."""

import matplotlib.pyplot as plt
import pandas as pd

from analysis.cornering.models import cornering_speed, sweep
from analysis_result import AnalysisResult

TITLE = "speed_vs_R"
DESCRIPTION = "Corner radius versus friction-limited speed: v = sqrt(mu_w * g * R)."
PLUGIN_ID = "speed_vs_r"
SPEED_RADIUS_MIN_M = 3.0
SPEED_RADIUS_MAX_M = 50.0
NUM_POINTS_SPEED_RADIUS = 200
PARAMETERS = {"mu_w": "float"}
OUTPUTS = {"cornering_speed_min_kmh": "Speed limit at the minimum sweep radius (km/h)",
           "cornering_speed_max_kmh": "Speed limit at the maximum sweep radius (km/h)"}


def main(parameters):
    radius = sweep(SPEED_RADIUS_MIN_M, SPEED_RADIUS_MAX_M, NUM_POINTS_SPEED_RADIUS, "Radius sweep")
    speed = cornering_speed(radius, parameters["mu_w"])
    figure, axis = plt.subplots(figsize=(8, 5))
    axis.plot(radius, speed * 3.6, linewidth=2)
    axis.set(xlabel="Corner Radius R (m)", ylabel="Maximum Speed (km/h)",
             title=r"Cornering Speed Limit ($v=\sqrt{\mu_y g R}$)")
    axis.grid(True)
    figure.tight_layout()
    outputs = {"cornering_speed_min_kmh": float(speed[0] * 3.6),
               "cornering_speed_max_kmh": float(speed[-1] * 3.6)}
    print(f"Cornering speed range: {speed[0] * 3.6:.2f}–{speed[-1] * 3.6:.2f} km/h")
    return AnalysisResult(figure, outputs,
                          tables={"cornering_speed.csv": pd.DataFrame({"radius_m": radius,
                                  "speed_mps": speed, "speed_kmh": speed * 3.6})},
                          figure_titles={"plot.png": "半徑與極限彎速"})
