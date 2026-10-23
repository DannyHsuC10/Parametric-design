"""The two direct force surfaces from new/friction_circle.py, using MF defaults."""

import matplotlib.pyplot as plt
import numpy as np

from analysis.Pacejka_tire_model import MF_tester
from analysis.Pacejka_tire_model.model.api import CalculationInput, MF_Universal_solver


def build_figures(tir_params, *, pressure, IA):
    # Match MF_tester's friction-circle demonstration sweeps.
    alpha, kappa = np.meshgrid(np.linspace(-10, 10, 50), np.linspace(-0.25, 0.25, 50))
    load_alpha, loads = np.meshgrid(np.linspace(-10, 10, 50),
                                   np.linspace(0, MF_tester.Fz_range[-1], 50))
    figures = {}
    try:
        for filename, fz, sa, sl, heights, title, zlabel, cmap, opacity in (
            ("Friction_Circle_vs_Slip_Ratio.png", MF_tester.Fz_fix, alpha, kappa, kappa,
             f"Friction Circle vs Slip Ratio (Fz = {MF_tester.Fz_fix:g} N)",
             "Slip Ratio κ", "viridis", 0.6),
            ("Friction_Circle_vs_Fz.png", loads, load_alpha, MF_tester.Slip_fix, loads,
             f"Friction Circle vs Vertical Load (κ = {MF_tester.Slip_fix:g})",
             "Vertical Load Fz [N]", "plasma", 1.0),
        ):
            calc = CalculationInput(FZ=fz, SA=sa, SL=sl, IA=IA, V=10,
                                    pressure=pressure, tir_params=tir_params)
            fx = MF_Universal_solver("FX", calc)
            fy = MF_Universal_solver("FY", calc)
            figure = plt.figure(figsize=(10, 6))
            figures[filename] = figure
            axis = figure.add_subplot(projection="3d")
            axis.plot_surface(fx, fy, heights, cmap=cmap, edgecolor="none", alpha=opacity)
            axis.set(xlabel="Fx [N]", ylabel="Fy [N]", zlabel=zlabel, title=title)
            figure.tight_layout()
        return figures
    except Exception:
        for figure in figures.values():
            plt.close(figure)
        raise
