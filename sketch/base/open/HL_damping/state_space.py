from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import signal

from heave_analysis import AxleHeaveResult, HeaveResult
from roll_analysis import RollResult
from vehicle import Axle, Vehicle


@dataclass(frozen=True)
class StateSpaceOutputs:
    roll_physical_low: signal.StateSpace
    roll_physical_high: signal.StateSpace
    roll_modal_low: signal.StateSpace
    roll_modal_high: signal.StateSpace
    roll_1dof_low: signal.StateSpace
    roll_1dof_high: signal.StateSpace
    physical_fit: pd.DataFrame


class StateSpaceAnalysis:
    def __init__(
        self,
        vehicle: Vehicle,
        heave: HeaveResult,
        roll: RollResult,
        output_dir: Path | None = None,
    ):
        self.vehicle = vehicle
        self.heave = heave
        self.roll = roll
        self.output_dir = output_dir or vehicle.output_dir

    def run(self) -> StateSpaceOutputs:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        ay_step = self.vehicle.analysis.roll_step_ay_g
        self._plot_heave_system(self.vehicle.front, self.heave.front)
        self._plot_heave_system(self.vehicle.rear, self.heave.rear)

        roll_modal_low = self._roll_system(self.roll.modal.damping_matrix_low)
        roll_modal_high = self._roll_system(self.roll.modal.damping_matrix_high)
        fit = self._fit_physical_roll_damping()
        roll_physical_low = self._roll_system(fit["low_matrix"])
        roll_physical_high = self._roll_system(fit["high_matrix"])
        roll_1dof_low = self._roll_1dof(zeta=self.roll.modal.target_zeta_low[0])
        roll_1dof_high = self._roll_1dof(zeta=self.roll.modal.target_zeta_high[0])

        self._plot_roll_steps(
            {
                "modal low": roll_modal_low,
                "modal high": roll_modal_high,
                "physical low": roll_physical_low,
                "physical high": roll_physical_high,
            }
        )
        self._plot_single_roll_step(
            roll_modal_low,
            f"Decoupled roll low-speed damping step, ay = {ay_step:.2f} g",
            "roll_step_low_speed.png",
            ay_step=ay_step,
        )
        self._plot_single_roll_step(
            roll_modal_high,
            f"Decoupled roll high-speed damping step, ay = {ay_step:.2f} g",
            "roll_step_high_speed.png",
            ay_step=ay_step,
        )
        self._plot_roll_bode(roll_modal_low, roll_modal_high)
        self._plot_single_roll_bode(
            roll_modal_low,
            "Decoupled roll low-speed damping bode",
            "roll_bode_low_speed.png",
        )
        self._plot_single_roll_bode(
            roll_modal_high,
            "Decoupled roll high-speed damping bode",
            "roll_bode_high_speed.png",
        )
        self._plot_roll_1dof(roll_1dof_low, roll_1dof_high, ay_step=ay_step)
        self._plot_roll_solution_comparison(
            roll_modal_low,
            roll_modal_high,
            roll_physical_low,
            roll_physical_high,
            roll_1dof_low,
            roll_1dof_high,
            ay_step=ay_step,
        )
        self._plot_tire_fz_transient(roll_physical_low, ay_step=ay_step)

        table = fit["table"]
        table.to_csv(self.output_dir / "roll_physical_damping_fit.csv", index=False)
        return StateSpaceOutputs(
            roll_physical_low=roll_physical_low,
            roll_physical_high=roll_physical_high,
            roll_modal_low=roll_modal_low,
            roll_modal_high=roll_modal_high,
            roll_1dof_low=roll_1dof_low,
            roll_1dof_high=roll_1dof_high,
            physical_fit=table,
        )

    def heave_system(self, axle: Axle, result: AxleHeaveResult) -> signal.StateSpace:
        ms = axle.sprung_mass_axis_kg
        mu = axle.unsprung_mass_axis_kg
        ks = result.wheel_rate_n_per_m
        kt = 2.0 * self.vehicle.tire_vertical_rate_n_per_m
        cs = result.low_speed_damping_n_s_per_m

        a = np.array(
            [
                [0.0, 1.0, 0.0, 0.0],
                [-ks / ms, -cs / ms, ks / ms, cs / ms],
                [0.0, 0.0, 0.0, 1.0],
                [ks / mu, cs / mu, -(ks + kt) / mu, -cs / mu],
            ]
        )
        b = np.array([[0.0], [0.0], [0.0], [kt / mu]])
        c = np.array([[1.0, 0.0, 0.0, 0.0]])
        d = np.array([[0.0]])
        return signal.StateSpace(a, b, c, d)

    def _plot_heave_system(self, axle: Axle, result: AxleHeaveResult) -> None:
        sys = self.heave_system(axle, result)
        t = np.linspace(0.0, 2.0, 900)
        tout, y = signal.step(sys, T=t)
        y = np.squeeze(y) * 0.02
        self._save_line(
            tout,
            y * 1000.0,
            f"{axle.name.title()} heave 20 mm road step",
            "time [s]",
            "sprung displacement [mm]",
            f"heave_{axle.name}_step.png",
        )

        w = np.logspace(-1, 2.2, 500)
        w, mag, phase = signal.bode(sys, w=w)
        fig, ax = plt.subplots(2, 1, sharex=True, figsize=(8, 6))
        ax[0].semilogx(w / (2 * np.pi), mag)
        ax[0].set_ylabel("magnitude [dB]")
        ax[0].grid(True, which="both")
        ax[1].semilogx(w / (2 * np.pi), phase)
        ax[1].set_xlabel("frequency [Hz]")
        ax[1].set_ylabel("phase [deg]")
        ax[1].grid(True, which="both")
        fig.suptitle(f"{axle.name.title()} heave bode")
        fig.tight_layout()
        fig.savefig(self.output_dir / f"heave_{axle.name}_bode.png", dpi=200)
        plt.close(fig)

    def _roll_system(self, damping: np.ndarray) -> signal.StateSpace:
        zero = np.zeros((3, 3))
        eye = np.eye(3)
        minv = np.linalg.inv(self.roll.mass_matrix)
        a = np.vstack(
            [
                np.hstack([zero, eye]),
                np.hstack(
                    [
                        -minv @ self.roll.stiffness_matrix,
                        -minv @ damping,
                    ]
                ),
            ]
        )
        b = np.zeros((6, 1))
        b[3, 0] = (
            self.vehicle.weight_n
            * self.roll.modal.sprung_to_roll_axis_height_m
            / self.vehicle.sprung_roll_inertia_kg_m2
        )
        c = np.array([[1.0, 0.0, 0.0, 0.0, 0.0, 0.0]])
        d = np.array([[0.0]])
        return signal.StateSpace(a, b, c, d)

    def _roll_1dof(self, zeta: float) -> signal.StateSpace:
        inertia = self.vehicle.sprung_roll_inertia_kg_m2
        stiffness = self.roll.total_roll_stiffness_n_m_per_rad
        damping = 2.0 * zeta * np.sqrt(stiffness * inertia)
        a = np.array([[0.0, 1.0], [-stiffness / inertia, -damping / inertia]])
        b = np.array(
            [[0.0], [self.vehicle.weight_n * self.roll.modal.sprung_to_roll_axis_height_m / inertia]]
        )
        c = np.array([[1.0, 0.0]])
        d = np.array([[0.0]])
        return signal.StateSpace(a, b, c, d)

    def _fit_physical_roll_damping(self) -> dict[str, object]:
        front_arm = self.vehicle.front.motion_ratio.roll * self.vehicle.front.track_m
        rear_arm = self.vehicle.rear.motion_ratio.roll * self.vehicle.rear.track_m
        front_basis = np.array([[1.0, -1.0, 0.0], [-1.0, 1.0, 0.0], [0.0, 0.0, 0.0]]) * front_arm**2
        rear_basis = np.array([[1.0, 0.0, -1.0], [0.0, 0.0, 0.0], [-1.0, 0.0, 1.0]]) * rear_arm**2

        rows = []
        matrices = {}
        for label, target in {
            "low": self.roll.modal.damping_matrix_low,
            "high": self.roll.modal.damping_matrix_high,
        }.items():
            basis = np.column_stack([front_basis.reshape(-1), rear_basis.reshape(-1)])
            coef, *_ = np.linalg.lstsq(basis, target.reshape(-1), rcond=None)
            fitted = coef[0] * front_basis + coef[1] * rear_basis
            matrices[f"{label}_matrix"] = fitted
            rows.append(
                {
                    "case": label,
                    "front_linear_damping_n_s_per_m": coef[0],
                    "rear_linear_damping_n_s_per_m": coef[1],
                    "fit_error_frobenius": np.linalg.norm(target - fitted),
                    "relative_fit_error": np.linalg.norm(target - fitted)
                    / np.linalg.norm(target),
                }
            )
        matrices["table"] = pd.DataFrame(rows)
        return matrices

    def _plot_roll_steps(self, systems: dict[str, signal.StateSpace]) -> None:
        t = np.linspace(0.0, 2.0, 900)
        unit_ay = self.vehicle.analysis.roll_unit_step_ay_g
        fig, ax = plt.subplots(figsize=(8, 4.8))
        for label, sys in systems.items():
            tout, y = signal.step(sys, T=t)
            ax.plot(tout, np.rad2deg(np.squeeze(y) * unit_ay), label=label)
        ax.set_title(f"Roll step response, ay = {unit_ay:.2f} g")
        ax.set_xlabel("time [s]")
        ax.set_ylabel("roll angle [deg]")
        ax.grid(True)
        ax.legend()
        fig.tight_layout()
        fig.savefig(self.output_dir / "roll_step_response.png", dpi=200)
        plt.close(fig)

    def _plot_single_roll_step(
        self,
        sys: signal.StateSpace,
        title: str,
        filename: str,
        ay_step: float,
    ) -> None:
        t = np.linspace(0.0, 2.0, 900)
        tout, y = signal.step(sys, T=t)
        fig, ax = plt.subplots(figsize=(8, 4.8))
        ax.plot(tout, np.rad2deg(np.squeeze(y) * ay_step), linewidth=2)
        ax.set_title(title)
        ax.set_xlabel("time [s]")
        ax.set_ylabel("roll angle [deg]")
        ax.grid(True)
        fig.tight_layout()
        fig.savefig(self.output_dir / filename, dpi=200)
        plt.close(fig)

    def _plot_roll_bode(self, low: signal.StateSpace, high: signal.StateSpace) -> None:
        w = np.logspace(-1, 2.2, 500)
        fig, ax = plt.subplots(2, 1, sharex=True, figsize=(8, 6))
        for label, sys in {"modal low": low, "modal high": high}.items():
            w, mag, phase = signal.bode(sys, w=w)
            ax[0].semilogx(w / (2 * np.pi), mag, label=label)
            ax[1].semilogx(w / (2 * np.pi), phase, label=label)
        ax[0].set_ylabel("magnitude [dB]")
        ax[1].set_xlabel("frequency [Hz]")
        ax[1].set_ylabel("phase [deg]")
        for item in ax:
            item.grid(True, which="both")
            item.legend()
        fig.suptitle("Roll bode")
        fig.tight_layout()
        fig.savefig(self.output_dir / "roll_bode_modal.png", dpi=200)
        plt.close(fig)

    def _plot_single_roll_bode(
        self,
        sys: signal.StateSpace,
        title: str,
        filename: str,
    ) -> None:
        w = np.logspace(-1, 2.2, 500)
        w, mag, phase = signal.bode(sys, w=w)
        fig, ax = plt.subplots(2, 1, sharex=True, figsize=(8, 6))
        ax[0].semilogx(w / (2 * np.pi), mag)
        ax[0].set_ylabel("magnitude [dB]")
        ax[0].grid(True, which="both")
        ax[1].semilogx(w / (2 * np.pi), phase)
        ax[1].set_xlabel("frequency [Hz]")
        ax[1].set_ylabel("phase [deg]")
        ax[1].grid(True, which="both")
        fig.suptitle(title)
        fig.tight_layout()
        fig.savefig(self.output_dir / filename, dpi=200)
        plt.close(fig)

    def _plot_roll_1dof(
        self,
        low: signal.StateSpace,
        high: signal.StateSpace,
        ay_step: float,
    ) -> None:
        t = np.linspace(0.0, 1.6, 700)
        fig, ax = plt.subplots(figsize=(8, 4.8))
        low_label = f"1DOF zeta {self.roll.modal.target_zeta_low[0]:.2f}"
        high_label = f"1DOF zeta {self.roll.modal.target_zeta_high[0]:.2f}"
        for label, sys in {low_label: low, high_label: high}.items():
            tout, y = signal.step(sys, T=t)
            ax.plot(tout, np.rad2deg(np.squeeze(y) * ay_step), label=label)
        ax.set_title(f"Equivalent 1DOF roll step, ay = {ay_step:.2f} g")
        ax.set_xlabel("time [s]")
        ax.set_ylabel("roll angle [deg]")
        ax.grid(True)
        ax.legend()
        fig.tight_layout()
        fig.savefig(self.output_dir / "roll_1dof_step.png", dpi=200)
        fig.savefig(self.output_dir / "fig3_13_roll_step_1dof.png", dpi=300)
        plt.close(fig)

        freq_hz = np.logspace(-1, 2.3, 1200)
        w = 2.0 * np.pi * freq_hz
        fig, ax = plt.subplots(2, 1, sharex=True, figsize=(8, 6))
        for label, sys in {low_label: low, high_label: high}.items():
            _, response = signal.freqresp(sys, w=w)
            _, _, phase = signal.bode(sys, w=w)
            ax[0].semilogx(freq_hz, np.abs(response) * 180.0 / np.pi, label=label)
            ax[1].semilogx(freq_hz, phase, label=label)
        static_roll_gradient = self.roll.total_roll_stiffness_n_m_per_rad
        static_roll_gradient = (
            self.vehicle.weight_n
            * self.roll.modal.sprung_to_roll_axis_height_m
            / static_roll_gradient
            * 180.0
            / np.pi
        )
        fn_1dof = np.sqrt(
            self.roll.total_roll_stiffness_n_m_per_rad
            / self.vehicle.sprung_roll_inertia_kg_m2
        ) / (2.0 * np.pi)
        ax[0].axhline(static_roll_gradient, color="black", linestyle="--", linewidth=1.0)
        ax[0].axvline(0.5, color="black", linestyle=":", linewidth=1.0)
        ax[0].axvline(2.0, color="black", linestyle=":", linewidth=1.0)
        ax[0].axvline(fn_1dof, color="magenta", linestyle="--", linewidth=1.0)
        ax[0].set_ylabel("magnitude [deg/g]")
        ax[0].grid(True, which="both")
        ax[0].legend()
        ax[1].set_xlabel("frequency [Hz]")
        ax[1].set_ylabel("phase [deg]")
        ax[1].axvline(0.5, color="black", linestyle=":", linewidth=1.0)
        ax[1].axvline(2.0, color="black", linestyle=":", linewidth=1.0)
        ax[1].axvline(fn_1dof, color="magenta", linestyle="--", linewidth=1.0)
        ax[1].grid(True, which="both")
        ax[1].legend()
        fig.suptitle("1DOF roll bode")
        fig.tight_layout()
        fig.savefig(self.output_dir / "roll_1dof_bode.png", dpi=200)
        fig.savefig(self.output_dir / "fig3_14_roll_bode_1dof.png", dpi=300)
        plt.close(fig)

    def _plot_roll_solution_comparison(
        self,
        modal_low: signal.StateSpace,
        modal_high: signal.StateSpace,
        physical_low: signal.StateSpace,
        physical_high: signal.StateSpace,
        one_dof_low: signal.StateSpace,
        one_dof_high: signal.StateSpace,
        ay_step: float,
    ) -> None:
        systems = [
            ("Low-speed damping comparison", modal_low, physical_low, one_dof_low),
            ("High-speed damping comparison", modal_high, physical_high, one_dof_high),
        ]
        t = np.linspace(0.0, 2.0, 900)
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), sharey=True)
        for ax, (title, modal, physical, one_dof) in zip(axes, systems):
            for label, sys, style in [
                ("modal", modal, "k--"),
                ("physical", physical, "b-"),
                ("1DOF", one_dof, "r-."),
            ]:
                tout, y = signal.step(sys, T=t)
                ax.plot(
                    tout,
                    np.rad2deg(np.squeeze(y) * ay_step),
                    style,
                    linewidth=1.8,
                    label=label,
                )
            ax.set_title(title)
            ax.set_xlabel("time [s]")
            ax.grid(True)
            ax.legend()
        axes[0].set_ylabel("roll angle [deg]")
        fig.suptitle(f"Roll response comparison: modal vs physical vs 1DOF, ay = {ay_step:.2f} g")
        fig.tight_layout()
        fig.savefig(self.output_dir / "roll_response_modal_physical_1dof.png", dpi=200)
        plt.close(fig)

    def _plot_tire_fz_transient(self, sys: signal.StateSpace, ay_step: float) -> None:
        t = np.linspace(0.0, 2.0, 900)
        ay = np.ones_like(t) * ay_step
        tout, _, x = signal.lsim(sys, U=ay, T=t)
        phi_uf = x[:, 1]
        phi_ur = x[:, 2]
        front_static = self.vehicle.weight_n * self.vehicle.front.weight_ratio / 2.0
        rear_static = self.vehicle.weight_n * self.vehicle.rear.weight_ratio / 2.0
        df_front = (
            self.vehicle.tire_vertical_rate_n_per_m
            * self.vehicle.front.track_m
            * phi_uf
            / 2.0
        )
        df_rear = (
            self.vehicle.tire_vertical_rate_n_per_m
            * self.vehicle.rear.track_m
            * phi_ur
            / 2.0
        )

        fig, ax = plt.subplots(figsize=(8, 4.8))
        ax.plot(tout, front_static + df_front, label="front outside")
        ax.plot(tout, front_static - df_front, label="front inside")
        ax.plot(tout, rear_static + df_rear, label="rear outside")
        ax.plot(tout, rear_static - df_rear, label="rear inside")
        ax.set_title(f"Transient tire Fz, {ay_step:.2f} g lateral step")
        ax.set_xlabel("time [s]")
        ax.set_ylabel("normal load [N]")
        ax.grid(True)
        ax.legend(ncol=2)
        fig.tight_layout()
        fig.savefig(self.output_dir / "roll_tire_fz_transient.png", dpi=200)
        plt.close(fig)

    def _save_line(
        self,
        x: np.ndarray,
        y: np.ndarray,
        title: str,
        xlabel: str,
        ylabel: str,
        filename: str,
    ) -> None:
        fig, ax = plt.subplots(figsize=(8, 4.8))
        ax.plot(x, y)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True)
        fig.tight_layout()
        fig.savefig(self.output_dir / filename, dpi=200)
        plt.close(fig)
