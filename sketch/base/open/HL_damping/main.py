from __future__ import annotations

import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pandas as pd
from scipy import signal

from damper import DamperAnalysis
from equivalent_independent import EquivalentIndependentAnalysis
from heave_analysis import HeaveAnalysis
from roll_analysis import RollAnalysis
from simulation import SimulationAnalysis
from state_space import StateSpaceAnalysis
from vehicle import make_default_vehicle


def main() -> None:
    vehicle = make_default_vehicle()
    output_dir = Path(__file__).resolve().parent / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    heave = HeaveAnalysis(vehicle).run()
    heave.to_frame().to_csv(output_dir / "heave_summary.csv", index=False)

    roll = RollAnalysis(vehicle).run()
    roll.to_frame().to_csv(output_dir / "roll_summary.csv", index=False)
    pd.DataFrame(
        {
            "mode": np.arange(1, 4),
            "natural_frequency_hz": roll.modal.natural_frequencies_hz,
            "target_zeta_low": roll.modal.target_zeta_low,
            "target_zeta_high": roll.modal.target_zeta_high,
        }
    ).to_csv(output_dir / "roll_modal_summary.csv", index=False)

    independent = EquivalentIndependentAnalysis(vehicle, heave, roll).run()
    independent.to_frame().to_csv(output_dir / "independent_equivalent.csv", index=False)

    state_space = StateSpaceAnalysis(vehicle, heave, roll, output_dir=output_dir).run()
    damper = DamperAnalysis(
        vehicle,
        heave,
        roll,
        independent,
        state_space,
        output_dir=output_dir,
    )
    damper_tables = damper.run()

    simulation = SimulationAnalysis(
        vehicle,
        heave,
        roll,
        independent,
        damper,
        output_dir=output_dir,
    )
    force_table = simulation.run()

    print("HL damping analysis complete.")
    print(f"Output directory: {output_dir}")
    print()
    print("--- Heave verification ---")
    print(f"Front heave natural frequency: {heave.front.natural_frequency_hz:.3f} Hz")
    print(f"Rear heave natural frequency: {heave.rear.natural_frequency_hz:.3f} Hz")
    print(f"Front heave low-speed damping ratio: {vehicle.front.heave_damping_ratio.low_average:.3f}")
    print(f"Front heave high-speed damping ratio: {vehicle.front.heave_damping_ratio.high_average:.3f}")
    print(f"Rear heave low-speed damping ratio: {vehicle.rear.heave_damping_ratio.low_average:.3f}")
    print(f"Rear heave high-speed damping ratio: {vehicle.rear.heave_damping_ratio.high_average:.3f}")
    print()
    front_heave_sys = StateSpaceAnalysis(vehicle, heave, roll, output_dir=output_dir).heave_system(
        vehicle.front,
        heave.front,
    )
    heave_modes = _damped_modes(front_heave_sys)
    print("--- State-space front heave dynamic response ---")
    print(f"Sprung mass frequency: {heave_modes[0, 0]:.3f} Hz")
    print(f"Unsprung mass frequency: {heave_modes[1, 0]:.3f} Hz")
    print(f"Sprung mass zeta: {heave_modes[0, 1]:.3f}")
    print()
    print("--- Roll verification ---")
    print(
        "Front actual roll stiffness: "
        f"{roll.front.actual_roll_stiffness_n_m_per_rad:.1f} Nm/rad "
        f"({roll.front.actual_roll_stiffness_n_m_per_rad / (180.0 / np.pi):.1f} Nm/deg)"
    )
    print(
        "Rear actual roll stiffness: "
        f"{roll.rear.actual_roll_stiffness_n_m_per_rad:.1f} Nm/rad "
        f"({roll.rear.actual_roll_stiffness_n_m_per_rad / (180.0 / np.pi):.1f} Nm/deg)"
    )
    print(f"Vehicle roll gradient: {roll.roll_gradient_deg_per_g:.3f} deg/g")
    print()
    print("--- Roll modal damping ---")
    print(f"Low-speed target modal zeta: {roll.modal.target_zeta_low[0]:.3f}")
    print(f"High-speed target modal zeta: {roll.modal.target_zeta_high[0]:.3f}")
    print(
        "Undamped roll modal frequencies: "
        + ", ".join(f"{item:.3f}" for item in roll.modal.natural_frequencies_hz)
        + " Hz"
    )
    print()
    ay_step = vehicle.analysis.roll_step_ay_g
    print(f"--- Roll state-space step response, ay = {ay_step:.2f} g ---")
    print(_step_metrics("modal low", state_space.roll_modal_low, ay_step=ay_step))
    print(_step_metrics("modal high", state_space.roll_modal_high, ay_step=ay_step))
    print(_step_metrics("physical low", state_space.roll_physical_low, ay_step=ay_step))
    print(_step_metrics("physical high", state_space.roll_physical_high, ay_step=ay_step))
    print(_step_metrics("1DOF low", state_space.roll_1dof_low, ay_step=ay_step))
    print(_step_metrics("1DOF high", state_space.roll_1dof_high, ay_step=ay_step))
    print()
    print("--- Independent suspension equivalent ---")
    print(independent.to_frame().to_string(index=False))
    print()
    print("--- Damper coefficients ---")
    for name, table in damper_tables.items():
        print(name)
        print(table.to_string(index=False))
    print()
    print("--- Roll physical damper fit ---")
    print(state_space.physical_fit.to_string(index=False))
    print()
    print("--- Spring force scenarios ---")
    print(force_table.to_string(index=False))


def _step_metrics(label: str, sys: signal.StateSpace, ay_step: float) -> str:
    t = np.linspace(0.0, 3.0, 1200)
    tout, y = signal.step(sys, T=t)
    y_deg = np.rad2deg(np.squeeze(y) * ay_step)
    final = _dcgain(sys) * ay_step * 180.0 / np.pi
    peak = np.max(y_deg)
    peak_time = tout[np.argmax(y_deg)]
    overshoot = 0.0 if abs(final) < 1e-12 else max((peak - final) / abs(final) * 100.0, 0.0)
    outside = np.where(np.abs(y_deg - final) > 0.02 * max(abs(final), 1e-12))[0]
    settling_time = tout[outside[-1] + 1] if len(outside) and outside[-1] + 1 < len(tout) else 0.0
    return (
        f"{label}: final={final:.3f} deg, peak={peak:.3f} deg, "
        f"peak_time={peak_time:.3f} s, overshoot={overshoot:.2f} %, "
        f"settling_time_approx={settling_time:.3f} s"
    )


def _dcgain(sys: signal.StateSpace) -> float:
    return (sys.C @ np.linalg.solve(-sys.A, sys.B) + sys.D).item()


def _damped_modes(sys: signal.StateSpace) -> np.ndarray:
    poles = np.linalg.eigvals(sys.A)
    modes = []
    for pole in poles:
        wn = abs(pole)
        if wn > 1e-12:
            zeta = -np.real(pole) / wn
            modes.append((wn / (2.0 * np.pi), zeta))
    modes.sort(key=lambda item: item[0])
    return np.asarray(modes)


if __name__ == "__main__":
    os.environ.setdefault("MPLBACKEND", "Agg")
    main()
