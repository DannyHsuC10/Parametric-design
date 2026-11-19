"""Adapt the saved map grid to upstream tire settings and export force limits."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from app.analysis_result import AnalysisResult
from analysis.Pacejka_tire_model.model.api import CalculationInput, MF_Universal_solver, load_tir
from .tire_mapping_tool import DEFAULT_OUTPUT, TireForceMap
from .tire_force_limit import get_fz_slice, get_fx_fy_boundary

DISPLAY_FZ_N = 800.0


def build_operating_map(pressure, camber, map_path=DEFAULT_OUTPUT):
    """Keep source axes, but recompute against the current TIR and tire settings.

    The supplied pickle has no TIR fingerprint, so even matching pressure/camber
    cannot establish that its tables represent the current input tire file.
    The original pickle is never overwritten.
    """
    if not np.isfinite(pressure) or pressure <= 0 or not np.isfinite(camber):
        raise ValueError("Tire pressure must be positive and camber must be finite")
    source = TireForceMap.load(map_path)
    fz, alpha, kappa = np.meshgrid(source.fz_axis, source.alpha_axis_deg, source.kappa_axis, indexing="ij")
    defaults = source.payload["metadata"]["defaults_used"]
    calc = CalculationInput(FZ=fz, SA=alpha, SL=kappa, IA=camber, pressure=pressure,
                            V=defaults["velocity"], Ro=defaults["rolling_radius"], tir_params=load_tir())
    tables = {key: np.asarray(MF_Universal_solver(key, calc)) for key in ("FX", "FY", "MZ")}
    tables["mu_total"] = np.hypot(tables["FX"], tables["FY"]) / fz
    if not all(np.isfinite(values).all() for values in tables.values()):
        raise ValueError("Tire mapping produced non-finite values")
    return TireForceMap({"axes": source.payload["axes"], "tables": tables})


def run_force_limit(parameters):
    pressure, camber = parameters["tire_pressure_Pa"], parameters["tire_camber_deg"]
    fz = DISPLAY_FZ_N
    tire_map = build_operating_map(pressure, camber)
    fz_slice = get_fz_slice(tire_map, fz)
    boundary = get_fx_fy_boundary(fz_slice)
    figure, axis = plt.subplots(figsize=(8, 7))
    axis.plot(boundary["FX"], boundary["FY"], color="red", linewidth=2.2)
    axis.set(xlabel="Fx [N]", ylabel="Fy [N]",
             title=f"Tire force limits: Fz={fz:g} N, camber={camber:g} deg, P={pressure:g} Pa")
    axis.set_aspect("equal", adjustable="box")
    axis.grid(True, linestyle=":")
    figure.tight_layout()
    print(f"Tire mapping boundary: pressure={pressure:g} Pa, camber={camber:g} deg; Fz={fz:g} N")
    return AnalysisResult(figure,
        tables={"fz_slice.csv": pd.DataFrame({name: values.ravel() for name, values in fz_slice.items()}),
                "fx_fy_boundary.csv": pd.DataFrame(boundary)},
        figure_titles={"plot.png": "輪胎力查表｜輪胎力極限範圍"})
