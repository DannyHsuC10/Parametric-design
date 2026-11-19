"""Analyze an exported lap recording; no simulator or upstream recalculation."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from app.analysis_result import AnalysisResult
from .plot_track_speed_map import build_speed_figure, load_speed_data

INPUT_FILE = Path(__file__).resolve().parents[2] / "data/input_data/steady_lapsim.pkl"
OUTPUTS = {
    "steady_lapsim_lap_time_s": "記錄時間跨度（s）",
    "steady_lapsim_distance_m": "記錄路程（m）",
    "steady_lapsim_average_speed_m_s": "路程／時間平均速度（m/s）",
    "steady_lapsim_min_speed_m_s": "最低車速（m/s）",
    "steady_lapsim_max_speed_m_s": "最高車速（m/s）",
    "steady_lapsim_sample_count": "記錄樣本數",
}


def run(input_path=None):
    path = INPUT_FILE if input_path is None else Path(input_path)
    data, metadata = load_speed_data(path)
    duration = float(np.ptp(data["time_s"]))
    distance = float(data["distance_m"][-1] - data["distance_m"][0])
    speed = data["speed_m_s"]
    if distance <= 0:
        raise ValueError("Recorded lap distance must be positive.")
    recorded_lap = metadata.get("lap_time_s")
    if recorded_lap is not None and (
        not np.isfinite(float(recorded_lap))
        or not np.isclose(float(recorded_lap), duration, rtol=1e-5, atol=1e-6)
    ):
        raise ValueError("Metadata lap_time_s differs from the recorded time span.")

    dt, ds = np.diff(data["time_s"]), np.diff(data["distance_m"])
    phases = []
    # Each interval belongs to its starting sample. The last sample has no interval.
    for phase in ("accelerate", "brake", "hold"):
        mask = data["phase"][:-1] == phase
        seconds, meters = float(dt[mask].sum()), float(ds[mask].sum())
        phases.append({"phase": phase, "time_s": seconds, "time_percent": seconds / duration * 100,
                       "distance_m": meters, "distance_percent": meters / distance * 100})
    phase_frame = pd.DataFrame(phases)
    outputs = dict(zip(OUTPUTS, (duration, distance, distance / duration,
                               float(speed.min()), float(speed.max()), len(speed))))
    overview, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
    colors = ["tab:green", "tab:red", "0.5"]
    for axis, name, label in zip(axes, ("time_percent", "distance_percent"),
                                ("Lap time [%]", "Lap distance [%]")):
        axis.bar(phase_frame["phase"], phase_frame[name], color=colors)
        axis.set(ylabel=label, title=label)
        axis.grid(axis="y", alpha=0.3)
    notes = (Path(__file__).with_name("README.md")).read_text(encoding="utf-8")
    notes += (f"\n## 本次記錄摘要\n\n"
              f"- 圈速：{duration:.6f} s\n- 路程：{distance:.3f} m\n"
              f"- 平均速度：{distance / duration:.3f} m/s（{distance / duration * 3.6:.3f} km/h）\n"
              f"- 速度範圍：{speed.min():.3f}–{speed.max():.3f} m/s\n"
              f"- 樣本數：{len(speed)}\n\n"
              "| 階段 | 時間（s） | 時間占比（%） | 路程（m） |\n|---|---:|---:|---:|\n")
    notes += "".join(f"| {r['phase']} | {r['time_s']:.3f} | {r['time_percent']:.2f} | {r['distance_m']:.3f} |\n"
                     for r in phases)
    print(f"Steady_lapsim: {duration:.6f} s, {distance:.3f} m, {len(speed)} samples")
    print(phase_frame.to_string(index=False))
    return AnalysisResult(
        build_speed_figure(data, metadata), outputs,
        figures={"phase_summary.png": overview},
        tables={"lap_samples.csv": pd.DataFrame(data), "phase_summary.csv": phase_frame},
        figure_titles={"plot.png": "賽道速度圖與加減速分布", "phase_summary.png": "各階段時間與路程占比"},
        artifacts={"analysis.md": notes},
    )
