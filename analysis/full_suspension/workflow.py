"""Run both original full-suspension cases and export results for the app."""

import json
import pickle
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import numpy as np
import pandas as pd
from PIL import Image, ImageSequence

from app.analysis_result import AnalysisResult
from .data_visualization.Dynamic_Visualizer_dashboard import SuspensionDashboard
from .data_visualization.Simulation_Logger import SimulationLogger
from .model import Suspension_model_v13 as model
from .suspension_set.Suspension import Suspension_A
from .suspension_set.suspension_state import full_suspension_state
from .suspension_set import all_road
from .parameters import applied_parameters

SCENARIOS = {"road_acc": all_road.road_acc, "road_FL_bump": all_road.road_FL_bump}
METRICS = {
    "peak_body_m": "車身角落最大絕對位移 (m)",
    "peak_acceleration_m_s2": "車身角落最大絕對加速度 (m/s²)",
    "peak_tire_force_N": "模型輪胎力最大絕對值 (N)",
    "peak_twist_deg": "最大絕對車架扭轉角 (deg)",
}
DURATION = 1.5
DT = 0.001
FPS = 8
DPI = 90
CORNERS = ("FL", "FR", "RL", "RR")
ATTITUDES = ("Front roll", "Rear roll", "Pitch", "Yaw")


def simulate(scenario, parameters=None):
    """Use a fresh vehicle/state for each case, matching new/lab_fullsus.py."""
    road = SCENARIOS[scenario]
    parameters = dict(parameters or {})
    suspension = Suspension_A(parameters)
    state = full_suspension_state(suspension, dt=DT)
    state.total_vehicle_mass_kg = suspension.m
    logger = SimulationLogger()
    logger.set_metadata(scenario=scenario, duration_s=DURATION, dt=DT,
                        wheel_order=CORNERS, attitude_order=ATTITUDES,
                        settings_source="analysis/full_suspension/suspension_set/Suspension.py",
                        upstream_parameters=parameters,
                        applied_model_parameters=applied_parameters(suspension))
    for _ in np.arange(0, DURATION, state.dt):
        road(state)
        model.motion(state, suspension)
        state.Integration(suspension)
        # Finite numbers alone do not detect unstable integration: the previous
        # inertia mapping produced 1e11-degree rolls without NaN/Inf.
        motion = (state.theta, state.omega, state.s, state.v, state.zu, state.vzu)
        if (not all(np.isfinite(value).all() for value in motion)
                or np.max(np.abs(state.theta[:3])) > np.pi / 4
                or abs(state.s[2]) > 1.0 or np.max(np.abs(state.zu)) > 1.0):
            raise ValueError(
                f"{scenario} t={state.t:.3f}s：響應發散或超出小角度模型範圍；"
                "請檢查慣量、KC 剛性／阻尼與積分步長。此工況不會輸出 GIF。")
        logger.add_state(state)
    data = logger.result()
    if not all(np.isfinite(value).all() for value in data.values()):
        raise ValueError(f"{scenario}: 模型產生非有限數值")
    return logger


def timeseries(data):
    """Flatten vector channels into named CSV columns without losing signals."""
    columns = {}
    for name, values in data.items():
        if values.ndim == 1:
            columns[name] = values
        else:
            labels = (ATTITUDES if name in {"theta", "omega", "alpha"} else
                      CORNERS if values.shape[1] == 4 else ("x", "y", "z"))
            for index, label in enumerate(labels):
                columns[f"{name}_{label.replace(' ', '_')}"] = values[:, index]
    return pd.DataFrame(columns)


def format_figure(figure, axes, title, labels):
    figure.suptitle(title)
    for axis, label in zip(axes, labels):
        axis.set_ylabel(label)
        axis.set_xlabel("Time (s)")
        axis.grid(alpha=0.3)
        axis.legend(fontsize=8)
    figure.tight_layout()


def response_figure(data, scenario):
    figure, axes = plt.subplots(4, 1, figsize=(11, 11), sharex=True)
    for index, corner in enumerate(CORNERS):
        for key, style in (("zs", "-"), ("zu", "--"), ("zr", ":")):
            axes[0].plot(data["t"], data[key][:, index], style, label=f"{corner} {key}")
        for axis, key in zip(axes[1:], ("vzs", "azs", "N")):
            axis.plot(data["t"], data[key][:, index], label=corner)
    format_figure(figure, axes, f"Full suspension / {scenario}",
                  ("Displacement (m)", "Body velocity (m/s)", "Body acceleration (m/s²)", "Signed tire force (N)"))
    return figure


def retime_gif(content):
    """Set GIF frame delays to preserve simulation time on its 10 ms clock."""
    with Image.open(BytesIO(content)) as source:
        frames = [frame.convert("RGB") for frame in ImageSequence.Iterator(source)]
    ticks = np.rint(np.linspace(0, DURATION * 100, len(frames) + 1)).astype(int)
    delays = (np.diff(ticks) * 10).tolist()
    output = BytesIO()
    frames[0].save(output, format="GIF", save_all=True, append_images=frames[1:],
                   duration=delays, loop=0)
    return output.getvalue()


def save_animation(data, scenario):
    viewer = SuspensionDashboard(data)
    try:
        viewer.fig.suptitle(f"Full suspension / {scenario}")
        viewer.ax_fz.set_title("Signed model tire force (N)")
        for axis, values in ((viewer.ax_fz, viewer.Fz), (viewer.ax_modal, viewer.modal)):
            low, high = min(0.0, float(values.min())), max(0.0, float(values.max()))
            padding = max(1.0, (high - low) * 0.1)
            axis.set_ylim(low - padding, high + padding)
        # Include both endpoints, with one frame per 1/FPS simulated seconds.
        frames = np.linspace(0, len(data["t"]) - 1, round(DURATION * FPS), dtype=int)
        animation = FuncAnimation(viewer.fig, viewer.update, frames=frames, interval=1000 / FPS, blit=False)
        temp_root = Path(__file__).resolve().parents[2] / "data/results"
        with TemporaryDirectory(dir=temp_root) as temporary:
            path = Path(temporary) / "dashboard.gif"
            animation.save(path, writer=PillowWriter(fps=FPS), dpi=DPI)
            return retime_gif(path.read_bytes())
    finally:
        plt.close(viewer.fig)


def run(parameters):
    overview, axes = plt.subplots(4, 1, figsize=(11, 11), sharex=True)
    result = AnalysisResult(overview)
    result.figure_titles["plot.png"] = "兩種工況｜車身姿態比較"
    summaries = []
    try:
        for scenario in SCENARIOS:
            print(f"Full suspension / {scenario}: simulation and GIF", flush=True)
            logger = simulate(scenario, parameters)
            data = logger.result()
            theta = np.rad2deg(data["theta"])
            roll = (theta[:, 0] + theta[:, 1]) / 2
            twist = theta[:, 0] - theta[:, 1]
            for axis, channel in zip(axes, (data["s"][:, 2], roll, theta[:, 2], twist)):
                axis.plot(data["t"], channel, label=scenario)
            summary = dict(peak_body_m=float(np.abs(data["zs"]).max()),
                           peak_acceleration_m_s2=float(np.abs(data["azs"]).max()),
                           peak_tire_force_N=float(np.abs(data["N"]).max()),
                           peak_twist_deg=float(np.abs(twist).max()))
            summaries.append({"scenario": scenario, **summary})
            result.outputs.update({f"full_suspension_{scenario}_{key}": value for key, value in summary.items()})
            result.tables[f"{scenario}_timeseries.csv"] = timeseries(data)
            result.artifacts[f"{scenario}.pkl"] = pickle.dumps({"data": data, "metadata": logger.metadata})
            result.artifacts[f"{scenario}_config.json"] = json.dumps(logger.metadata, ensure_ascii=False, indent=2)
            result.figures[f"{scenario}_response.png"] = response_figure(data, scenario)
            result.figure_titles[f"{scenario}_response.png"] = f"{scenario}｜四輪響應與輪胎力"
            result.artifacts[f"{scenario}.gif"] = save_animation(data, scenario)
            result.figure_titles[f"{scenario}.gif"] = f"{scenario}｜Dashboard GIF"
        result.outputs["full_suspension_case_count"] = len(SCENARIOS)
        result.tables["case_summary.csv"] = pd.DataFrame(summaries)
        format_figure(overview, axes, "Full suspension / both scenarios",
                      ("Body heave (m)", "Mean roll (deg)", "Pitch (deg)", "Chassis twist (deg)"))
        return result
    except BaseException:
        result.close()
        raise
