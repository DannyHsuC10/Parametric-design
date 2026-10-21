"""Track-analysis entry point for the shared analysis flow and result gallery."""

from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd

from analysis_result import AnalysisResult
from analysis.track_analysis.geometry import (
    ascii_map, build_track, create_figures, radius_distributions, read_workbook,
)
from analysis.track_analysis.score_weight import calculate_score_weights, create_score_figure
from analysis.track_analysis.track_data import TrackData


TITLE = "賽道分析"
DESCRIPTION = "Reconstruct track geometry, analyze curvature and radius distributions, and weight event scores."
PLUGIN_ID = "track_analysis"
INPUT_MAP = Path(__file__).resolve().parents[1] / "data" / "input_data" / "input_map.xlsx"
PARAMETER_DEFAULTS = {
    "track_mesh_size_m": 0.1,
    "track_max_speed_kmh": 110.0,
    "track_radius_limit_m": 100.0,
    "wl_mu_y": 1.7,
    "track_skidpad_score": 75.0,
    "track_autocross_score": 100.0,
    "track_endurance_score": 250.0,
}
PARAMETERS = {name: "float" for name in PARAMETER_DEFAULTS}
OUTPUTS = {
    "track_length_m": "Total centerline length (m)",
    "track_points": "Number of generated mesh points",
    "track_apex_count": "Number of detected curvature peaks",
    "track_minimum_radius_m": "Minimum smoothed corner radius (m; 0 if no corners)",
    "track_average_radius_m": "Distance-weighted radius within the selected limit (m; 0 if none)",
    "track_corner_length_m": "Distance within the selected corner-radius limit (m)",
    "track_corner_time_s": "Estimated time within the selected corner-radius limit (s)",
    "track_top_5_score_rate_percent": "Share of the event-score pool in the top five radius bins (%)",
}
FIGURE_TITLES = {
    "plot.png": "主要結果｜賽道平面與曲率",
    "radius.png": "曲率與 Apex",
    "curvature_fft_frequency.png": "曲率頻譜｜空間頻率",
    "curvature_fft_wavelength.png": "曲率頻譜｜空間波長",
    "radius_time_distribution.png": "轉彎半徑｜時間分布",
    "radius_length_distribution.png": "轉彎半徑｜距離分布",
    "radius_score_weight.png": "轉彎半徑｜分數權重",
    "elevation.png": "賽道高程",
    "inclination.png": "賽道坡度",
    "banking.png": "賽道傾角",
    "grip_factor.png": "抓地係數",
}


def main(parameters, *, input_path=None):
    values = PARAMETER_DEFAULTS | parameters
    mesh_size = values["track_mesh_size_m"]
    max_speed = values["track_max_speed_kmh"] / 3.6
    radius_limit = values["track_radius_limit_m"]
    info, segments, tables = read_workbook(Path(input_path) if input_path is not None else INPUT_MAP)
    track = build_track(segments, tables, mesh_size)
    lengths, times = radius_distributions(track, max_speed, radius_limit, values["wl_mu_y"])
    nonzero = np.abs(track["r"]) > 1e-9
    radii = np.full_like(track["r"], np.nan)
    radii[nonzero] = 1.0 / np.abs(track["r"][nonzero])
    corners = nonzero & (radii <= radius_limit)
    minimum_radius = float(np.min(radii[nonzero])) if np.any(nonzero) else None
    average_radius = (float(np.average(radii[corners], weights=track["dx"][corners]))
                      if np.any(corners) else None)
    summary = TrackData(
        Skidpad_score=values["track_skidpad_score"],
        Autocross_score=values["track_autocross_score"],
        Endurance_score=values["track_endurance_score"],
        Track_length=float(track["x"][-1]), Average_radius=average_radius,
        Name=info["name"], Country=info["country"], Track_points=int(track["n"]),
        Mesh_size=mesh_size, Apex_count=len(track["apex_index"]),
        track_Minimum_radius=minimum_radius,
        Radius_distribution_length=lengths, Radius_distribution_time=times,
    )
    scores = calculate_score_weights(summary)
    outputs = {
        "track_length_m": summary.Track_length,
        "track_points": summary.Track_points,
        "track_apex_count": summary.Apex_count,
        "track_minimum_radius_m": minimum_radius or 0.0,
        "track_average_radius_m": average_radius or 0.0,
        "track_corner_length_m": sum(item["accumulated_length_m"] for item in lengths),
        "track_corner_time_s": sum(item["accumulated_time_s"] for item in times),
        "track_top_5_score_rate_percent": summary.top_5_score_rate,
    }
    figures = create_figures(track, lengths, times)
    primary = figures.pop("xy_map.png")
    figures["radius_score_weight.png"] = create_score_figure(scores)
    buffer = BytesIO()
    np.savez_compressed(buffer, **track, **{f"info_{key}": np.asarray(value) for key, value in info.items()})
    log = (f"OpenTRACK Python\nInput: {input_path or INPUT_MAP}\nName: {info['name']}\n"
           + "\n".join(f"{name}: {value}" for name, value in outputs.items()) + "\n")
    print(log, end="")
    print("Radius time uses v = min(sqrt(wl_mu_y * g * R), maximum speed).")
    return AnalysisResult(
        primary, outputs, figures=figures, figure_titles=FIGURE_TITLES,
        tables={
            "radius_distribution_length.csv": pd.DataFrame(lengths),
            "radius_distribution_time.csv": pd.DataFrame(times),
            "radius_distribution_score.csv": pd.DataFrame(scores, columns=[
                "rank", "radius_range_m", "radius_center_m", "accumulated_time_s",
                "weight_ratio", "weighted_score", "skidpad_bonus", "total_score",
            ]),
        },
        artifacts={"OpenTRACK.npz": buffer.getvalue(), "track.json": summary.to_json(),
                   "OpenTRACK.log": log + "\nMap:\n" + ascii_map(track) + "\n"},
    )
