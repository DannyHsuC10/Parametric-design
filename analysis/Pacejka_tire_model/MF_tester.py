"""Generate all 19 MF_tester charts without import-time I/O or GUI calls.

The sweeps and force models follow new/Pacejka_tire_model/MF_tester.py.
Evaluate whole grids with NumPy instead of evaluating individual points.
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
from scipy.interpolate import griddata

from .model.api import CalculationInput, MF_Universal_solver, load_tir

OUTPUTS = ("FX", "FY", "MX", "MZ", "RRT")
FIX_CASES = ("alpha", "kappa", "Fz")
Slip_range = np.linspace(-1, 1, 50)
alpha_range = np.linspace(-12, 12, 50)
Fz_range = np.linspace(0, 1400, 50)
Slip_fix, alpha_fix, Fz_fix = 0.1, 6.0, 800.0


def fig_set(fix, out):
    if fix == "alpha":
        return "Slip ratio", "Fz [N]", out, Slip_range, Fz_range
    if fix == "kappa":
        return "Slip angle [deg]", "Fz [N]", out, alpha_range, Fz_range
    if fix == "Fz":
        return "Slip ratio", "Slip angle [deg]", out, Slip_range, alpha_range
    raise ValueError(f"Unknown fixed variable: {fix}")


def MF_set(i, j, X, Y, fix, tir_params, pressure=82319, IA=0.0):
    x, y = X[i, j], Y[i, j]
    settings = {
        "alpha": dict(FZ=y, SA=alpha_fix, SL=x),
        "kappa": dict(FZ=y, SA=x, SL=Slip_fix),
        "Fz": dict(FZ=Fz_fix, SA=y, SL=x),
    }
    return CalculationInput(**settings[fix], IA=IA, pressure=pressure, tir_params=tir_params)


def plot_tire_surfaces(out, fix, tir_params_list, labels=None, save_plt=False,
                       *, pressure=82319, IA=0.0, output_dir=None):
    xlabel, ylabel, zlabel, x_range, y_range = fig_set(fix, out)
    X, Y = np.meshgrid(x_range, y_range)
    figure = plt.figure(figsize=(10, 6))
    axis = figure.add_subplot(projection="3d")
    legends = []
    for index, params in enumerate(tir_params_list):
        calc = MF_set(slice(None), slice(None), X, Y, fix, params, pressure, IA)
        Z = np.broadcast_to(MF_Universal_solver(out, calc), X.shape)
        cmap = plt.get_cmap(("viridis", "plasma", "inferno", "cividis", "magma")[index % 5])
        axis.plot_surface(X, Y, Z, cmap=cmap, edgecolor="none", alpha=0.6)
        legends.append(Patch(facecolor=cmap(0.6), label=labels[index] if labels else f"Tire {index+1}"))
    axis.set(xlabel=xlabel, ylabel=ylabel, zlabel=zlabel, title=f"{out} - Tire Model Comparison")
    axis.legend(handles=legends)
    figure.tight_layout()
    if save_plt:
        destination = Path(output_dir) if output_dir else Path(__file__).parent / "Figures"
        destination.mkdir(parents=True, exist_ok=True)
        figure.savefig(destination / f"{out}_{fix}fix.png", dpi=200, bbox_inches="tight")
    return figure


def _friction_maps(Fz, alpha, kappa, pressure, tir_params, IA):
    calc = CalculationInput(FZ=Fz, SA=alpha, SL=kappa, IA=IA,
                            pressure=pressure, tir_params=tir_params)
    return (np.asarray(MF_Universal_solver("FX", calc)),
            np.asarray(MF_Universal_solver("FY", calc)))


def _friction_figure(fx, fy, heights, title, zlabel, surface, cmap="viridis"):
    figure = plt.figure(figsize=(10, 6))
    axis = figure.add_subplot(projection="3d")
    if surface:
        points = np.column_stack((fx.ravel(), fy.ravel()))
        X, Y = np.meshgrid(np.linspace(fx.min(), fx.max(), 100),
                           np.linspace(fy.min(), fy.max(), 100))
        Z = griddata(points, np.broadcast_to(heights, fx.shape).ravel(), (X, Y), method="linear")
        plotted = axis.plot_surface(X, Y, Z, cmap=cmap, edgecolor="none", alpha=0.8)
        figure.colorbar(plotted, ax=axis, shrink=0.5, aspect=10)
    else:
        for x, y, z in zip(fx, fy, np.broadcast_to(heights, fx.shape)):
            axis.plot(x, y, z, color="blue", alpha=0.7)
    axis.set(xlabel="Fx [N]", ylabel="Fy [N]", zlabel=zlabel, title=title)
    figure.tight_layout()
    return figure


def plot_friction_circle_vs_kappa_surface(Fz=800, pressure=82319, alpha_lim=10,
                                          kappa_lim=0.25, tir_params=None, IA=0.0, show_plot=False):
    alpha, kappa = np.meshgrid(np.linspace(-alpha_lim, alpha_lim, 50),
                               np.linspace(-kappa_lim, kappa_lim, 50))
    fx, fy = _friction_maps(Fz, alpha, kappa, pressure, tir_params, IA)
    return _friction_figure(fx, fy, kappa, "Friction Circle vs Slip Ratio - Surface", "Slip ratio", True)


def plot_friction_circle_vs_kappa_curves(Fz=800, pressure=82319, alpha_lim=10,
                                         kappa_lim=0.25, tir_params=None, IA=0.0, show_plot=False):
    alpha, kappa = np.meshgrid(np.linspace(-alpha_lim, alpha_lim, 200),
                               np.linspace(-kappa_lim, kappa_lim, 200))
    fx, fy = _friction_maps(Fz, alpha, kappa, pressure, tir_params, IA)
    return _friction_figure(fx, fy, kappa, "Friction Circle vs Slip Ratio - Curves", "Slip ratio", False)


def plot_friction_circle_vs_Fz_surface(kappa=0.1, pressure=82319, alpha_lim=10,
                                      Fz_max=1400, tir_params=None, IA=0.0, show_plot=False):
    alpha, fz = np.meshgrid(np.linspace(-alpha_lim, alpha_lim, 50), np.linspace(0, Fz_max, 50))
    fx, fy = _friction_maps(fz, alpha, kappa, pressure, tir_params, IA)
    return _friction_figure(fx, fy, fz, "Friction Circle vs Fz - Surface", "Fz [N]", True, "plasma")


def plot_friction_circle_vs_Fz_curves(kappa=0.1, alpha_lim=10, Fz_max=1400,
                                     pressure=82319, tir_params=None, IA=0.0, show_plot=False):
    fz, alpha = np.meshgrid(np.linspace(0, Fz_max, 50), np.linspace(-alpha_lim, alpha_lim, 400))
    fx, fy = _friction_maps(fz, alpha, kappa, pressure, tir_params, IA)
    return _friction_figure(fx, fy, fz, "Friction Circle vs Fz - Curves", "Fz [N]", False)


def build_figures(tir_params, *, pressure=82319, IA=0.0):
    """Return the 15 force/moment surfaces and four friction-circle charts."""
    figures = {}
    try:
        for out in OUTPUTS:
            for fix in FIX_CASES:
                figures[f"{out}_{fix}fix.png"] = plot_tire_surfaces(
                    out, fix, [tir_params], pressure=pressure, IA=IA)
                print(f"MF_tester: {out}_{fix}fix")
        for filename, function in (
            ("Friction_Circle_vs_Slip_Ratio_face.png", plot_friction_circle_vs_kappa_surface),
            ("Friction_Circle_vs_Slip_Ratio_curves.png", plot_friction_circle_vs_kappa_curves),
            ("Friction_Circle_vs_Fz_face.png", plot_friction_circle_vs_Fz_surface),
            ("Friction_Circle_vs_Fz_curves.png", plot_friction_circle_vs_Fz_curves),
        ):
            figures[filename] = function(tir_params=tir_params, pressure=pressure, IA=IA)
            print(f"MF_tester: {filename}")
        return figures
    except Exception:
        for figure in figures.values():
            plt.close(figure)
        raise


if __name__ == "__main__":
    destination = Path(__file__).parent / "Figures"
    destination.mkdir(parents=True, exist_ok=True)
    for filename, figure in build_figures(load_tir()).items():
        figure.savefig(destination / filename, dpi=200, bbox_inches="tight")
        plt.close(figure)
