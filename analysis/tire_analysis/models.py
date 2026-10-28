"""Numerical sweeps matching the source tire scripts, with angles in degrees."""

import numpy as np

from analysis.Pacejka_tire_model.model.api import CalculationInput, MF_Universal_solver, load_tir

PSI_TO_PA = 6894.757293168
PRESSURES_PSI = np.arange(8.0, 15.0)
CAMBERS_DEG = np.linspace(-3.0, 3.0, 25)  # 0.25 deg intervals, including both endpoints.
SLIP_RATIOS = np.linspace(-1, 1, 61)
SLIP_ANGLES_DEG = np.linspace(-10, 10, 61)
LOADS_N = np.linspace(0, 1400, 61)


def force_surface(params, output, slips, loads, pressure, camber):
    slip_grid, load_grid = np.meshgrid(slips, loads)
    if not np.isfinite(pressure) or pressure <= 0:
        raise ValueError("胎壓必須是大於零的有限數值（Pa）")
    if not np.isfinite(camber):
        raise ValueError("camber 必須是有限數值（deg）")
    calc = CalculationInput(FZ=load_grid, SA=slip_grid if output == "FY" else 0.0,
                            SL=slip_grid if output == "FX" else 0.0,
                            IA=camber, pressure=pressure, tir_params=params)
    force = np.asarray(MF_Universal_solver(output, calc))
    if not np.all(np.isfinite(force)):
        raise ValueError(f"{output} 輪胎模型產生非有限數值，請檢查 TIR 參數")
    return force


def optimize_lateral(params, candidates, *, pressure=None):
    """Maximize Fy RMS across the original 61 x 61 alpha/load grid."""
    surfaces = np.array([
        force_surface(params, "FY", SLIP_ANGLES_DEG, LOADS_N,
                      candidate * PSI_TO_PA if pressure is None else pressure,
                      0.0 if pressure is None else candidate)
        for candidate in candidates
    ])
    rms = np.sqrt(np.mean(surfaces**2, axis=(1, 2)))
    return int(np.argmax(rms)), rms, surfaces


def friction_peaks(params, pressure, camber):
    """Origin-constrained fit of peak force vs load, excluding Fz=0."""
    results = {}
    for direction, slips in (("x", SLIP_RATIOS), ("y", np.linspace(-10, 10, 81))):
        force = force_surface(params, f"F{direction.upper()}", slips, LOADS_N, pressure, camber)
        # Original Fx script uses the positive driving maximum; Fy uses |Fy|.
        indices = np.argmax(force if direction == "x" else np.abs(force), axis=1)
        peak = np.abs(force[np.arange(len(LOADS_N)), indices])
        nonzero = LOADS_N > 0
        loads, peaks = LOADS_N[nonzero], peak[nonzero]
        coefficient = float(np.dot(loads, peaks) / np.dot(loads, loads))
        mu_curve = peaks / loads
        if not np.isfinite(coefficient) or coefficient <= 0:
            raise ValueError(f"mu_{direction} 必須大於零，請檢查 TIR 參數")
        results[direction] = dict(force=force, slips=slips, peak=peak,
                                  peak_slip=slips[indices], coefficient=coefficient,
                                  peak_mu=float(np.max(mu_curve)), mu_curve=mu_curve)
    return results
