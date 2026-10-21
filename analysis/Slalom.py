"""Slalom path geometry adapted from new/Slalom.py for the analysis workflow."""

import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle
import pandas as pd

from analysis.cornering.models import slalom_geometry
from analysis_result import AnalysisResult

TITLE = "Slalom"
DESCRIPTION = "依前輪距、角錐間距與偏移量，比較連續過彎的圓弧走線與半徑。"
PLUGIN_ID = "slalom"
# Fixed course geometry; the UI only exposes the shared front track t.
TRACK_WIDTH_M = 10.0
OFFSET_RATIOS = (0.01, 0.16666666666666666, 0.3333333333333333)
CONE_RADIUS_M = 0.16122034611053285
DRIVING_ERROR_M = 0.2
CONE_GAP_M = 7.0
NUM_CONES = 5
TIRE_WIDTH_M = 0.1905
PARAMETERS = {"t": "float"}
OUTPUTS = {
    "slalom_min_curve_radius_m": "Minimum circular path radius across the offset cases (m)",
    "slalom_max_curve_radius_m": "Maximum circular path radius across the offset cases (m)",
    "slalom_clearance_radius_m": "Front half-track + tire half-width + cone radius + driving margin (m)",
}


def main(parameters):
    wheel_track = parameters["t"]
    ratios = OFFSET_RATIOS
    count = NUM_CONES
    if not isinstance(count, int) or count < 2:
        raise ValueError("Slalom requires at least two cones")
    gap = CONE_GAP_M
    offsets, clearance, radii, angles = slalom_geometry(
        TRACK_WIDTH_M, ratios, wheel_track, CONE_RADIUS_M, DRIVING_ERROR_M, gap, TIRE_WIDTH_M,
    )

    figures, titles = {}, {}
    for start in range(0, len(offsets), 4):
        stop = min(start + 4, len(offsets))
        figure, axes = plt.subplots(stop - start, 1, figsize=(15, 3.2 * (stop - start)),
                                    squeeze=False, constrained_layout=True)
        for index, axis in zip(range(start, stop), axes[:, 0]):
            offset, radius, angle = offsets[index], radii[index], angles[index]
            for cone in range(count):
                # Alternate by cone index, including the zero-offset case.
                side = (-1) ** cone
                x, y = cone * gap, side * offset
                axis.add_patch(Circle((x, y), clearance, edgecolor="royalblue",
                                      facecolor="none", linewidth=1.5,
                                      label="Vehicle / cone clearance" if cone == 0 else None))
                axis.plot(x, y, "o", color="darkorange", markersize=4,
                          label="Cone center" if cone == 0 else None)
                theta1, theta2 = ((angle, 180 - angle) if side > 0
                                  else (180 + angle, -angle))
                axis.add_patch(Arc((x, y + (clearance - radius) * side),
                                   2 * radius, 2 * radius, theta1=theta1, theta2=theta2,
                                   color="black", linewidth=2,
                                   label="Circular path" if cone == 0 else None))
            axis.set(xlabel="X (m)", ylabel="Y (m)",
                     title=f"Slalom: offset={offset:.3f} m ({ratios[index]:.4g}), "
                           f"front track={wheel_track:.3f} m, R={radius:.3f} m")
            axis.grid(True, alpha=0.4)
            axis.autoscale()
            axis.set_xlim(-gap, gap * count + 1)
            axis.set_aspect("equal")
            axis.legend(loc="upper right", fontsize=8)
        filename = "plot.png" if start == 0 else f"slalom_paths_{start // 4 + 1}.png"
        figures[filename] = figure
        titles[filename] = f"Slalom 連續過彎走線（偏移組合 {start + 1}–{stop}）"

    frame = pd.DataFrame({
        "offset_ratio": ratios, "offset_m": offsets, "front_track_m": wheel_track,
        "clearance_radius_m": clearance, "curve_radius_m": radii, "arc_angle_deg": angles,
    })
    print(frame.to_string(index=False))
    return AnalysisResult(
        figures.pop("plot.png"),
        {"slalom_min_curve_radius_m": float(radii.min()),
         "slalom_max_curve_radius_m": float(radii.max()),
         "slalom_clearance_radius_m": float(clearance)},
        figures=figures, tables={"slalom_geometry.csv": frame}, figure_titles=titles,
    )
