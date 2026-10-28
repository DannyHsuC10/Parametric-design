"""AnalysisResult adapters; all persistence is handled by the shared saver."""

import json

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

from app.analysis_result import AnalysisResult
from analysis.Pacejka_tire_model import MF_tester
from analysis.Pacejka_tire_model.model.api import TIRE_FILE
from .models import (PSI_TO_PA, PRESSURES_PSI, CAMBERS_DEG, SLIP_ANGLES_DEG,
                     LOADS_N, force_surface, friction_peaks, load_tir, optimize_lateral)

MODEL_PRESSURE_PA = 82319.0
MODEL_CAMBER_DEG = 0.0


def run_friction_circle(p):
    from .friction_circle import build_figures

    figures = build_figures(load_tir(), pressure=MODEL_PRESSURE_PA, IA=MODEL_CAMBER_DEG)
    return AnalysisResult(
        figures["Friction_Circle_vs_Slip_Ratio.png"],
        {"friction_circle_figure_count": len(figures)}, figures=figures,
        figure_titles={"plot.png": "摩擦圓｜滑移率曲面",
                       "Friction_Circle_vs_Slip_Ratio.png": "摩擦圓｜滑移率曲面",
                       "Friction_Circle_vs_Fz.png": "摩擦圓｜垂直載荷曲面"})


def run_model(p):
    figures = MF_tester.build_figures(load_tir(), pressure=MODEL_PRESSURE_PA, IA=MODEL_CAMBER_DEG)
    # Keep every original filename, plus the shared gallery's plot.png shortcut.
    primary = figures["FY_kappafix.png"]
    titles = {"plot.png": "輪胎模型｜FY（固定滑移率）"}
    for filename in figures:
        titles[filename] = filename.removesuffix(".png")
    return AnalysisResult(primary, {"tire_model_figure_count": len(figures)}, figures=figures,
                          figure_titles=titles)


def run_optimization(p, *, camber=False):
    params = load_tir()
    candidates = CAMBERS_DEG if camber else PRESSURES_PSI
    best, rms, surfaces = optimize_lateral(
        params, candidates, pressure=p["tire_pressure_Pa"] if camber else None)
    name = "Camber" if camber else "Pressure"
    label = "Camber [deg]" if camber else "Tire pressure [psi]"
    figure, axis = plt.subplots(figsize=(8, 5))
    axis.plot(candidates, rms, marker="o")
    axis.scatter([candidates[best]], [rms[best]], color="red", zorder=4, label=f"Best: {candidates[best]:g}")
    axis.set(xlabel=label, ylabel="RMS Fy [N]", title=f"Tire Performance vs {name} (Fy RMS)")
    axis.grid(True)
    axis.legend()
    figure.tight_layout()
    surface = plt.figure(figsize=(10, 8))
    ax = surface.add_subplot(projection="3d")
    angles, loads = np.meshgrid(SLIP_ANGLES_DEG, LOADS_N)
    colors = ("red", "orange", "gold", "green", "blue", "indigo", "violet")
    if camber:
        colors = plt.get_cmap("turbo")(np.linspace(0, 1, len(candidates)))
    for values, color in zip(surfaces, colors):
        ax.plot_surface(loads, angles, values, color=color, alpha=0.25, linewidth=0)
    ax.legend(handles=[Patch(facecolor=color, label=f"{candidate:g} {'deg' if camber else 'psi'}")
                       for candidate, color in zip(candidates, colors)],
              ncol=3 if camber else 1, fontsize="small" if camber else "medium",
              loc="upper right" if camber else "best")
    ax.set(xlabel="Normal load Fz [N]", ylabel="Slip angle [deg]", zlabel="Fy [N]",
           title=f"Magic Formula Tire Fy Surface vs {name}")
    surface.tight_layout()
    if camber:
        outputs = {"tire_camber_deg": float(candidates[best]), "tire_camber_rms_Fy_N": float(rms[best])}
        rms_filename = "Tire_Performance_vs_Camber_RMS.png"
    else:
        outputs = {"tire_pressure_psi": float(candidates[best]),
                   "tire_pressure_Pa": float(candidates[best] * PSI_TO_PA),
                   "tire_pressure_rms_Fy_N": float(rms[best])}
        rms_filename = "Tire_Performance_vs_Pressure_RMS_Criterion_Fy.png"
    surface_filename = f"Magic_Formula_Tire_Fy_Surface_vs_{name}.png"
    print(f"Best {name}: {candidates[best]:g}; RMS Fy: {rms[best]:.3f} N")
    # Store the original RMS filename too, so source chart names remain available.
    return AnalysisResult(figure, outputs, figures={surface_filename: surface, rms_filename: figure},
                          tables={f"tire_{name.lower()}_rms.csv": pd.DataFrame({
                              "camber_deg" if camber else "pressure_psi": candidates,
                              "rms_Fy_N": rms, "selected": np.arange(len(candidates)) == best})},
                          figure_titles={"plot.png": f"最佳{name}｜Fy RMS",
                                         surface_filename: f"Fy 曲面｜{name}", rms_filename: f"Fy RMS｜{name}"})


def _line(x, y, xlabel, ylabel, title):
    figure, axis = plt.subplots(figsize=(7, 5))
    axis.plot(x, y, linewidth=2)
    axis.set(xlabel=xlabel, ylabel=ylabel, title=title)
    axis.grid(True)
    figure.tight_layout()
    return figure


def run_friction(p):
    params = load_tir()
    pressure, camber = p["tire_pressure_Pa"], p["tire_camber_deg"]
    peaks = friction_peaks(params, pressure, camber)
    figures, tables, outputs = {}, {}, {}
    summary, axes = plt.subplots(1, 2, figsize=(12, 5))
    nonzero = LOADS_N > 0
    for index, direction in enumerate(("x", "y")):
        data = peaks[direction]
        name = f"F{direction}"
        slip_label = "Slip ratio" if direction == "x" else "Slip angle [deg]"
        slip_name = "Slip Ratio" if direction == "x" else "Slip Angle"
        figures[f"Peak {name} vs Fz.png"] = _line(LOADS_N, data["peak"], "Fz [N]", f"Peak |{name}| [N]", f"Peak {name} vs Fz")
        figures[f"Peak {slip_name} vs Fz.png"] = _line(LOADS_N, np.abs(data["peak_slip"]), "Fz [N]", slip_label, f"Peak {slip_name} vs Fz")
        figures[f"Peak Friction Coefficient {name}.png"] = _line(
            LOADS_N[nonzero], data["mu_curve"], "Fz [N]", f"Peak mu_{direction}", f"Peak Friction Coefficient {name}")
        regression = _line(LOADS_N[nonzero], data["peak"][nonzero], "Fz [N]", f"Peak |{name}| [N]", "Linear Regression Through Origin")
        for ax in (regression.axes[0], axes[index]):
            ax.plot(LOADS_N[nonzero], data["peak"][nonzero], "o", label="Magic Formula")
            ax.plot(LOADS_N[nonzero], data["coefficient"] * LOADS_N[nonzero], label=f"Origin fit: mu_{direction}={data['coefficient']:.4f}")
            ax.legend()
            ax.grid(True)
            ax.set(xlabel="Fz [N]", ylabel=f"Peak |{name}| [N]")
        figures[f"Linear Regression Through Origin {name}.png"] = regression
        surface = plt.figure(figsize=(9, 7))
        ax = surface.add_subplot(projection="3d")
        slips, loads = np.meshgrid(data["slips"], LOADS_N)
        plotted = ax.plot_surface(slips, loads, data["force"], cmap="viridis")
        ax.set(xlabel=slip_label, ylabel="Fz [N]", zlabel=f"{name} [N]", title=f"Magic Formula Tire {name} Surface")
        surface.colorbar(plotted, ax=ax, shrink=0.6)
        surface.tight_layout()
        figures[f"Magic Formula Tire {name} Surface.png"] = surface
        curve_slips = np.linspace(0, 1 if direction == "x" else 10, 101)
        curve_loads = np.linspace(100, 1400, 8)
        force = force_surface(params, f"F{direction.upper()}", curve_slips, curve_loads, pressure, camber)
        curves, ax = plt.subplots(figsize=(8, 6))
        for load, values in zip(curve_loads, force):
            ax.plot(curve_slips, values / load, label=f"Fz={load:.0f} N")
        ax.set(xlabel=slip_label, ylabel=f"mu_{direction}", title=f"mu_{direction} vs {slip_name}")
        ax.grid(True)
        ax.legend()
        curves.tight_layout()
        figures[f"μ{direction}_vs_{slip_name.replace(' ', '_')}.png"] = curves
        tables[f"mu_{direction}_peaks.csv"] = pd.DataFrame({"Fz_N": LOADS_N,
            "peak_force_N": data["peak"], "peak_slip": data["peak_slip"],
            "peak_mu": np.divide(data["peak"], LOADS_N, out=np.full_like(LOADS_N, np.nan), where=nonzero)})
        outputs[f"mu_{direction}_RL"] = data["coefficient"]
        outputs[f"mu_{direction}_max"] = data["peak_mu"]
        print(f"mu_{direction}: origin fit={data['coefficient']:.4f}; maximum={data['peak_mu']:.4f}")
    outputs.update(mu_w=outputs["mu_x_RL"], wl_mu_y=outputs["mu_y_RL"])
    summary.suptitle(f"Tire Friction - {pressure / PSI_TO_PA:g} psi, camber {camber:g} deg")
    summary.tight_layout()
    tire_json = json.dumps({"tir_file": TIRE_FILE.name, "Tire_Pressure": pressure,
                            "camber": camber, **outputs}, ensure_ascii=False, allow_nan=False, indent=2)
    return AnalysisResult(summary, outputs, figures=figures, tables=tables,
                          figure_titles={"plot.png": "縱向／橫向摩擦係數回歸", **{name: name[:-4] for name in figures}},
                          artifacts={"tire.json": tire_json})
