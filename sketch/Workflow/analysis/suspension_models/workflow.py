"""Run only one model's compatible cases and return a complete result gallery."""

import json
import pickle

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from app.analysis_result import AnalysisResult
from . import batch_cases, batch_runner

from .parameters import SCENARIO_TITLES, STAGES, make_suspension, scenarios_for


def corner_channels(family):
    return ("",) if family == "quarter" else (("left_", "right_") if family == "LR" else ("front_", "rear_"))


def metrics(data, family):
    corners = corner_channels(family)
    return {
        "peak_body_m": float(max(np.max(np.abs(data[f"{corner}zs"])) for corner in corners)),
        "peak_acceleration_m_s2": float(max(np.max(np.abs(data[f"{corner}azs"])) for corner in corners)),
        "peak_tire_force_N": float(max(np.max(np.abs(data[f"{corner}Ft"])) for corner in corners)),
    }


def body_motion(data, family, model, suspension):
    if family == "quarter":
        return data["zs"], data["azs"], None
    first, second = corner_channels(family)
    if family == "LR":
        heave = (data[f"{first}zs"] + data[f"{second}zs"]) / 2
        if not batch_cases.FAMILIES[family].models[model].supports_cornering:
            angle = (data["left_zs"] - data["right_zs"]) / suspension.track
        else:
            angle = data["roll"]
    else:
        heave = (data["front_zs"] * suspension.lr + data["rear_zs"] * suspension.lf) / suspension.l
        angle = data["pitch"]
    acceleration = (data[f"{first}azs"] + data[f"{second}azs"]) / 2
    return heave, acceleration, angle


def finish_figure(figure, axes, title):
    figure.suptitle(title)
    for axis in np.ravel(axes):
        axis.set_xlabel("Time (s)")
        axis.grid(alpha=0.3)
        if axis.lines:
            axis.legend(fontsize=8)
    figure.tight_layout()


def case_figure(data, family, model, scenario):
    figure, axes = plt.subplots(4, 1, figsize=(11, 11), sharex=True)
    time = data["t"]
    for corner in corner_channels(family):
        label = corner.rstrip("_") or "quarter"
        for key, style in (("zs", "-"), ("zu", "--"), ("zr", ":")):
            axes[0].plot(time, data[corner + key], style, label=f"{label} {key}")
        for key in ("vzs", "vzu", "vzr"):
            axes[1].plot(time, data[corner + key], label=f"{label} {key}")
        for key in ("azs", "azu"):
            axes[2].plot(time, data[corner + key], label=f"{label} {key}")
        for key in ("Fs", "Ft"):
            axes[3].plot(time, data[corner + key], label=f"{label} {key}")
    for axis, label in zip(axes, ("Displacement (m)", "Velocity (m/s)", "Acceleration (m/s²)", "Model force (N)")):
        axis.set_ylabel(label)
    finish_figure(figure, axes, f"{family} / {model} / {scenario}")
    return figure


def body_figure(data, family, model, scenario, suspension):
    figure, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
    heave, _, angle = body_motion(data, family, model, suspension)
    axes[0].plot(data["t"], heave, label="Geometric body heave")
    axes[0].set_ylabel("Heave (m)")
    axes[1].plot(data["t"], np.rad2deg(angle), label="Roll" if family == "LR" else "Pitch")
    axes[1].set_ylabel("Body angle (deg)")
    if family == "LR" and model == "rollcenter_all":
        axes[2].plot(data["t"], data["d_frame"], label="Frame deformation")
        axes[2].set_ylabel("Frame displacement (m)")
    else:
        moment = "Mx" if family == "LR" else "My"
        axes[2].plot(data["t"], data[moment], label=moment)
        axes[2].set_ylabel("Body moment (N m)")
    finish_figure(figure, axes, f"{family} / {model} / {scenario} | body motion")
    return figure


def frame_figure(data, scenario):
    figure, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
    axes[0].plot(data["t"], data["F_frame_cmd"], "--", label="RC force command")
    axes[0].plot(data["t"], data["F_frame_spring"], label="Body spring force")
    axes[0].plot(data["t"], data["F_frame_damper"], label="Body damping force")
    axes[0].plot(data["t"], data["dF_roll"], label="Transmitted RC force")
    axes[0].set_ylabel("Force (N)")
    axes[1].plot(data["t"], data["d_frame"], label="Equivalent body-spring displacement")
    axes[1].set_ylabel("Displacement (m)")
    axes[2].plot(data["t"], data["v_frame"], label="Equivalent body-spring velocity")
    axes[2].set_ylabel("Velocity (m/s)")
    finish_figure(figure, axes, f"LR / rollcenter_all / {scenario} | RC body-spring branch")
    return figure


def run_stage(stage, parameters):
    family, model, title = STAGES[stage]
    scenarios = scenarios_for(stage)
    overview, axes = plt.subplots(4, 1, figsize=(11, 11), sharex=True)
    result = AnalysisResult(overview)
    result.figure_titles["plot.png"] = "全部工況｜響應比較"
    summaries, configs = [], []
    try:
        for index, scenario in enumerate(scenarios, 1):
            print(f"  [{index}/{len(scenarios)}] {family}/{model}/{scenario}：計算與靜態圖表", flush=True)
            suspension = make_suspension(family, parameters)
            suspension, state, road, function, config = batch_runner.prepare_case(
                family, model, scenario, dt=batch_cases.DEFAULT_DT, suspension=suspension,
            )
            config["upstream_parameters"] = dict(parameters)
            logger = batch_runner.simulate_case(suspension, state, road, function, config)
            data = logger.result()
            summary = metrics(data, family)
            summaries.append({"scenario": scenario, "工況": SCENARIO_TITLES.get(scenario, scenario), **summary})
            configs.append(config)
            result.outputs.update({f"{stage}_{scenario}_{key}": value for key, value in summary.items()})
            result.tables[f"{scenario}_timeseries.csv"] = pd.DataFrame(data)
            result.artifacts[f"{scenario}.pkl"] = pickle.dumps({"data": data, "metadata": logger.metadata})
            result.artifacts[f"{scenario}_config.json"] = json.dumps(config, ensure_ascii=False, indent=2)
            label = SCENARIO_TITLES.get(scenario, scenario)
            filename = f"{scenario}_response.png"
            result.figures[filename] = case_figure(data, family, model, scenario)
            result.figure_titles[filename] = f"{label}｜位移、速度、加速度與力"
            if family != "quarter":
                filename = f"{scenario}_body.png"
                result.figures[filename] = body_figure(data, family, model, scenario, suspension)
                result.figure_titles[filename] = f"{label}｜車身姿態"
            if family == "LR" and model == "rollcenter_all":
                filename = f"{scenario}_frame.png"
                result.figures[filename] = frame_figure(data, scenario)
                result.figure_titles[filename] = f"{label}｜RC 車體彈簧傳力與變形"
            heave, acceleration, angle = body_motion(data, family, model, suspension)
            axes[0].plot(data["t"], heave, label=scenario)
            axes[1].plot(data["t"], acceleration, label=scenario)
            # Plot both channels: a single max envelope hides force direction.
            for corner in corner_channels(family):
                axes[2].plot(data["t"], data[corner + "Ft"], label=f"{scenario} {corner.rstrip('_')}")
            if angle is None:
                axes[3].plot(data["t"], data["zs"] - data["zr"], label=scenario)
            else:
                axes[3].plot(data["t"], np.rad2deg(angle), label=scenario)
        result.outputs[f"{stage}_case_count"] = len(scenarios)
        for axis, label in zip(axes, ("Body heave (m)", "Body acceleration (m/s²)", "Model tire force (N)",
                                     "Body-road displacement (m)" if family == "quarter" else "Body angle (deg)")):
            axis.set_ylabel(label)
        finish_figure(overview, axes, f"{family} / {model} | all compatible scenarios")
        result.tables["case_summary.csv"] = pd.DataFrame(summaries)
        result.tables["suspension_parameters.csv"] = pd.DataFrame([
            {"parameter": name, "value": value} for name, value in configs[0]["suspension_parameters"].items()
        ])
        result.artifacts["cases.json"] = json.dumps(configs, ensure_ascii=False, indent=2)
        return result
    except BaseException:
        result.close()
        raise


