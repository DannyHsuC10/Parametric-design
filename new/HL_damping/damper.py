from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from equivalent_independent import IndependentResult
from heave_analysis import HeaveResult
from roll_analysis import RollResult
from state_space import StateSpaceOutputs
from vehicle import Axle, Vehicle


@dataclass(frozen=True)
class DamperCurve:
    low_bump_n_per_mm_s: float
    low_rebound_n_per_mm_s: float
    high_bump_n_per_mm_s: float
    high_rebound_n_per_mm_s: float
    knee_velocity_mm_s: float

    def force(self, velocity_mm_s: np.ndarray | float) -> np.ndarray:
        v = np.asarray(velocity_mm_s, dtype=float)
        force = np.zeros_like(v)

        bump = v >= 0.0
        rebound = ~bump
        force[bump] = self._side_force(
            v[bump],
            self.low_bump_n_per_mm_s,
            self.high_bump_n_per_mm_s,
            sign=1.0,
        )
        force[rebound] = self._side_force(
            np.abs(v[rebound]),
            self.low_rebound_n_per_mm_s,
            self.high_rebound_n_per_mm_s,
            sign=-1.0,
        )
        return force

    def _side_force(
        self,
        speed: np.ndarray,
        low_slope: float,
        high_slope: float,
        sign: float,
    ) -> np.ndarray:
        low_region = np.minimum(speed, self.knee_velocity_mm_s) * low_slope
        high_region = np.maximum(speed - self.knee_velocity_mm_s, 0.0) * high_slope
        return sign * (low_region + high_region)


class DamperAnalysis:
    def __init__(
        self,
        vehicle: Vehicle,
        heave: HeaveResult,
        roll: RollResult,
        independent: IndependentResult,
        state_space: StateSpaceOutputs,
        output_dir: Path | None = None,
    ):
        self.vehicle = vehicle
        self.heave = heave
        self.roll = roll
        self.independent = independent
        self.state_space = state_space
        self.output_dir = output_dir or vehicle.output_dir

    def run(self) -> dict[str, pd.DataFrame]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        decoupled = self._heave_curves(independent=False)
        independent = self._heave_curves(independent=True)
        roll = self._roll_physical_curves()
        roll_1dof = self._roll_1dof_curves()

        self._plot_curves(decoupled, "Decoupled heave shock dyno", "shock_dyno_decoupled_heave.png")
        self._plot_curves(independent, "Independent equivalent shock dyno", "shock_dyno_independent.png")
        self._plot_curves(roll, "Physical roll shock dyno", "shock_dyno_roll_physical.png")
        self._plot_roll_solution_compare(roll_1dof, roll)

        tables = {
            "damper_decoupled.csv": self._curve_table(decoupled),
            "damper_independent.csv": self._curve_table(independent),
            "damper_roll_physical.csv": self._curve_table(roll),
            "damper_roll_1dof.csv": self._curve_table(roll_1dof),
        }
        for filename, frame in tables.items():
            frame.to_csv(self.output_dir / filename, index=False)
        return tables

    def damper_curve_for_axle(self, axle: Axle, independent: bool = False) -> DamperCurve:
        heave = self.heave.front if axle.name == "front" else self.heave.rear
        divider = 2.0 if independent else 1.0
        mr = axle.motion_ratio.independent if independent else axle.motion_ratio.heave
        scale = divider * mr**2 * 1000.0
        return DamperCurve(
            low_bump_n_per_mm_s=heave.critical_damping_n_s_per_m
            * axle.heave_damping_ratio.low_bump
            / scale,
            low_rebound_n_per_mm_s=heave.critical_damping_n_s_per_m
            * axle.heave_damping_ratio.low_rebound
            / scale,
            high_bump_n_per_mm_s=heave.critical_damping_n_s_per_m
            * axle.heave_damping_ratio.high_bump
            / scale,
            high_rebound_n_per_mm_s=heave.critical_damping_n_s_per_m
            * axle.heave_damping_ratio.high_rebound
            / scale,
            knee_velocity_mm_s=self.vehicle.analysis.damper_knee_velocity_mm_s,
        )

    def _heave_curves(self, independent: bool) -> dict[str, DamperCurve]:
        return {
            "front": self.damper_curve_for_axle(self.vehicle.front, independent=independent),
            "rear": self.damper_curve_for_axle(self.vehicle.rear, independent=independent),
        }

    def _roll_physical_curves(self) -> dict[str, DamperCurve]:
        fit = self.state_space.physical_fit.set_index("case")
        front_low = fit.loc["low", "front_linear_damping_n_s_per_m"]
        rear_low = fit.loc["low", "rear_linear_damping_n_s_per_m"]
        front_high = fit.loc["high", "front_linear_damping_n_s_per_m"]
        rear_high = fit.loc["high", "rear_linear_damping_n_s_per_m"]

        return {
            "front": DamperCurve(
                low_bump_n_per_mm_s=front_low / 1000.0,
                low_rebound_n_per_mm_s=front_low / 1000.0,
                high_bump_n_per_mm_s=front_high / 1000.0,
                high_rebound_n_per_mm_s=front_high / 1000.0,
                knee_velocity_mm_s=self.vehicle.analysis.damper_knee_velocity_mm_s,
            ),
            "rear": DamperCurve(
                low_bump_n_per_mm_s=rear_low / 1000.0,
                low_rebound_n_per_mm_s=rear_low / 1000.0,
                high_bump_n_per_mm_s=rear_high / 1000.0,
                high_rebound_n_per_mm_s=rear_high / 1000.0,
                knee_velocity_mm_s=self.vehicle.analysis.damper_knee_velocity_mm_s,
            ),
        }

    def _roll_1dof_curves(self) -> dict[str, DamperCurve]:
        roll_k = self.roll.total_roll_stiffness_n_m_per_rad
        inertia = self.vehicle.sprung_roll_inertia_kg_m2
        c_phi_low = 2.0 * self.roll.modal.target_zeta_low[0] * np.sqrt(roll_k * inertia)
        c_phi_high = 2.0 * self.roll.modal.target_zeta_high[0] * np.sqrt(roll_k * inertia)
        front_dist = self.roll.front.roll_stiffness_distribution
        rear_dist = self.roll.rear.roll_stiffness_distribution
        front_arm = self.vehicle.front.motion_ratio.roll * self.vehicle.front.track_m
        rear_arm = self.vehicle.rear.motion_ratio.roll * self.vehicle.rear.track_m
        front_low = c_phi_low * front_dist / front_arm**2
        rear_low = c_phi_low * rear_dist / rear_arm**2
        front_high = c_phi_high * front_dist / front_arm**2
        rear_high = c_phi_high * rear_dist / rear_arm**2

        return {
            "front": DamperCurve(
                low_bump_n_per_mm_s=front_low / 1000.0,
                low_rebound_n_per_mm_s=front_low / 1000.0,
                high_bump_n_per_mm_s=front_high / 1000.0,
                high_rebound_n_per_mm_s=front_high / 1000.0,
                knee_velocity_mm_s=self.vehicle.analysis.damper_knee_velocity_mm_s,
            ),
            "rear": DamperCurve(
                low_bump_n_per_mm_s=rear_low / 1000.0,
                low_rebound_n_per_mm_s=rear_low / 1000.0,
                high_bump_n_per_mm_s=rear_high / 1000.0,
                high_rebound_n_per_mm_s=rear_high / 1000.0,
                knee_velocity_mm_s=self.vehicle.analysis.damper_knee_velocity_mm_s,
            ),
        }

    def _curve_table(self, curves: dict[str, DamperCurve]) -> pd.DataFrame:
        rows = []
        for name, curve in curves.items():
            rows.append(
                {
                    "axle": name,
                    "low_bump_n_per_mm_s": curve.low_bump_n_per_mm_s,
                    "low_rebound_n_per_mm_s": curve.low_rebound_n_per_mm_s,
                    "high_bump_n_per_mm_s": curve.high_bump_n_per_mm_s,
                    "high_rebound_n_per_mm_s": curve.high_rebound_n_per_mm_s,
                    "knee_velocity_mm_s": curve.knee_velocity_mm_s,
                }
            )
        return pd.DataFrame(rows)

    def _plot_curves(
        self,
        curves: dict[str, DamperCurve],
        title: str,
        filename: str,
    ) -> None:
        velocity = np.linspace(-250.0, 250.0, 501)
        fig, ax = plt.subplots(figsize=(8, 4.8))
        for label, curve in curves.items():
            ax.plot(velocity, curve.force(velocity), label=label)
        ax.axhline(0.0, color="black", linewidth=0.8)
        ax.axvline(0.0, color="black", linewidth=0.8)
        ax.set_title(title)
        ax.set_xlabel("shaft velocity [mm/s]")
        ax.set_ylabel("damper force [N]")
        ax.grid(True)
        ax.legend()
        fig.tight_layout()
        fig.savefig(self.output_dir / filename, dpi=200)
        plt.close(fig)

    def _plot_roll_solution_compare(
        self,
        solution_1: dict[str, DamperCurve],
        solution_2: dict[str, DamperCurve],
    ) -> None:
        velocity = np.linspace(-250.0, 250.0, 501)
        fig, axes = plt.subplots(1, 2, figsize=(9, 4.8), sharey=True)
        for ax, axle in zip(axes, ["front", "rear"]):
            ax.plot(
                velocity,
                solution_1[axle].force(velocity),
                "r-.",
                linewidth=1.8,
                label="solution 1, 1DOF",
            )
            ax.plot(
                velocity,
                solution_2[axle].force(velocity),
                "b-",
                linewidth=2.0,
                label="solution 2, physical fit",
            )
            ax.axhline(0.0, color="black", linewidth=0.8)
            ax.axvline(0.0, color="black", linewidth=0.8)
            ax.set_title(f"{axle.title()} roll damper")
            ax.set_xlabel("shaft velocity [mm/s]")
            ax.grid(True)
            ax.legend()
        axes[0].set_ylabel("damper force [N]")
        fig.suptitle("Roll damper dyno comparison: solution 1 vs solution 2")
        fig.tight_layout()
        fig.savefig(self.output_dir / "shock_dyno_roll_solution_compare.png", dpi=200)
        plt.close(fig)
