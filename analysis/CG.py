"""CG-height limits for the two geometric tilt angles in the supplied script."""

import matplotlib.pyplot as plt
import numpy as np

TITLE = "CG"
DESCRIPTION = "比較目前重心高度與 45°／60° 傾斜幾何上限。"
PLUGIN_ID = "cg"
PARAMETERS = dict.fromkeys(("t", "hl_rear_track_m", "h_cog", "cog_total_mass_kg", "cg_safety_factor"), "float")
HIDDEN_PARAMETERS = {"cog_total_mass_kg"}
PARAMETER_DEFAULTS = {"cg_safety_factor": 1.1}
OUTPUTS = {"cg_height_limit_45_m": "45 degree CG height limit with safety factor (m)",
           "cg_height_limit_60_m": "60 degree CG height limit with safety factor (m)",
           "cg_height_margin_60_m": "60 degree height limit minus current CG height (m)"}


def main(parameters):
    if not all(np.isfinite(value) for value in parameters.values()):
        raise ValueError("CG 參數必須為有限數值")
    if min(parameters[name] for name in ("t", "hl_rear_track_m", "cog_total_mass_kg")) <= 0:
        raise ValueError("輪距與總質量必須大於零")
    if parameters["cg_safety_factor"] < 1 or parameters["h_cog"] < 0:
        raise ValueError("cg_safety_factor 必須至少為 1，h_cog 不可為負數")
    width = min(parameters["t"], parameters["hl_rear_track_m"])
    widths = np.linspace(min(.8, width * .8), max(1.6, width * 1.2), 300)
    figure, axis = plt.subplots(figsize=(9, 6), layout="constrained")
    limits = {}
    for angle in (45, 60):
        heights = widths / (2 * np.tan(np.deg2rad(angle)) * parameters["cg_safety_factor"])
        limits[angle] = float(width / (2 * np.tan(np.deg2rad(angle)) * parameters["cg_safety_factor"]))
        axis.plot(widths, heights, label=f"Tilt angle {angle} deg")
        axis.scatter(width, limits[angle])
    axis.axvline(width, linestyle="--", color="gray", label=f"Min. axle track {width:g} m")
    axis.scatter(width, parameters["h_cog"], color="red", marker="X", s=100, label="Current CG height")
    axis.set(xlabel="Track width [m]", ylabel="CG height [m]",
             title=f"CG height / geometric tilt limits | SF = {parameters['cg_safety_factor']:g}")
    axis.grid(alpha=.3)
    axis.legend()
    outputs = {"cg_height_limit_45_m": limits[45], "cg_height_limit_60_m": limits[60],
               "cg_height_margin_60_m": limits[60] - parameters["h_cog"]}
    print(f"CG height: {parameters['h_cog']:.4f} m; 60 deg limit: {limits[60]:.4f} m")
    return figure, outputs
