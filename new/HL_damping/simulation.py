from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp

from damper import DamperAnalysis, DamperCurve
from equivalent_independent import IndependentResult
from heave_analysis import HeaveResult
from roll_analysis import RollResult
from vehicle import Axle, ScenarioSetting, Vehicle, format_g_tag


class SimulationAnalysis:
    def __init__(
        self,
        vehicle: Vehicle,
        heave: HeaveResult,
        roll: RollResult,
        independent: IndependentResult,
        damper: DamperAnalysis,
        output_dir: Path | None = None,
    ):
        self.vehicle = vehicle
        self.heave = heave
        self.roll = roll
        self.independent = independent
        self.damper = damper
        self.output_dir = output_dir or vehicle.output_dir

    def run(self) -> pd.DataFrame:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        scenarios = self.vehicle.analysis.scenarios
        table = pd.DataFrame([self._calc_scenario(item) for item in scenarios])
        table.to_csv(self.output_dir / "spring_force_scenarios.csv", index=False)

        braking_g = self.vehicle.analysis.ode_braking_g
        acceleration_g = self.vehicle.analysis.ode_acceleration_g
        braking = self._plot_longitudinal_ode(
            ax_g=-braking_g,
            filename=f"ode_braking_{format_g_tag(braking_g)}g.png",
            comparison_filename=f"nonlinear_braking_{format_g_tag(braking_g)}g_comparison.png",
        )
        acceleration = self._plot_longitudinal_ode(
            ax_g=acceleration_g,
            filename=f"ode_acceleration_{format_g_tag(acceleration_g)}g.png",
            comparison_filename=f"nonlinear_acceleration_{format_g_tag(acceleration_g)}g_comparison.png",
        )
        self._plot_decoupled_longitudinal_comparison(braking, acceleration)
        return table

    def _calc_scenario(self, scenario: ScenarioSetting) -> dict[str, float | str]:
        front_static = (
            self.vehicle.sprung_mass_kg
            * self.vehicle.front.weight_ratio
            * self.vehicle.gravity_mps2
        )
        rear_static = (
            self.vehicle.sprung_mass_kg
            * self.vehicle.rear.weight_ratio
            * self.vehicle.gravity_mps2
        )
        longitudinal_transfer = (
            scenario.ax_g
            * self.vehicle.weight_n
            * self.vehicle.cg_height_m
            / self.vehicle.wheelbase_m
        )

        front_load = front_static - longitudinal_transfer
        rear_load = rear_static + longitudinal_transfer
        front_heave = self.heave.front.wheel_rate_n_per_m
        rear_heave = self.heave.rear.wheel_rate_n_per_m
        front_spring_stroke_mm = (
            front_load / front_heave * self.vehicle.front.motion_ratio.heave * 1000.0
        )
        rear_spring_stroke_mm = (
            rear_load / rear_heave * self.vehicle.rear.motion_ratio.heave * 1000.0
        )
        front_pitch_dz = -longitudinal_transfer / self.heave.front.ride_rate_n_per_m
        rear_pitch_dz = longitudinal_transfer / self.heave.rear.ride_rate_n_per_m
        pitch_deg = np.rad2deg(
            np.arctan2(front_pitch_dz - rear_pitch_dz, self.vehicle.wheelbase_m)
        )

        roll_angle_rad = (
            scenario.ay_g
            * self.vehicle.weight_n
            * self.roll.modal.sprung_to_roll_axis_height_m
            / self.roll.total_roll_stiffness_n_m_per_rad
        )
        front_susp_share = (
            self.roll.front.actual_roll_stiffness_n_m_per_rad
            / self.roll.front.suspension_roll_stiffness_n_m_per_rad
        )
        rear_susp_share = (
            self.roll.rear.actual_roll_stiffness_n_m_per_rad
            / self.roll.rear.suspension_roll_stiffness_n_m_per_rad
        )
        front_roll_travel = (
            front_susp_share
            * roll_angle_rad
            * self.vehicle.front.motion_ratio.roll
            * self.vehicle.front.track_m
        )
        rear_roll_travel = (
            rear_susp_share
            * roll_angle_rad
            * self.vehicle.rear.motion_ratio.roll
            * self.vehicle.rear.track_m
        )

        return {
            "case": scenario.name,
            "ax_g": scenario.ax_g,
            "ay_g": scenario.ay_g,
            "front_sprung_axis_load_n": front_load,
            "rear_sprung_axis_load_n": rear_load,
            "front_heave_spring_stroke_mm": front_spring_stroke_mm,
            "rear_heave_spring_stroke_mm": rear_spring_stroke_mm,
            "pitch_deg": pitch_deg,
            "roll_deg": np.rad2deg(roll_angle_rad),
            "front_roll_suspension_travel_mm": front_roll_travel * 1000.0,
            "rear_roll_suspension_travel_mm": rear_roll_travel * 1000.0,
            "front_heave_spring_force_n": front_spring_stroke_mm
            * self.vehicle.front.spring.heave_n_per_mm,
            "rear_heave_spring_force_n": rear_spring_stroke_mm
            * self.vehicle.rear.spring.heave_n_per_mm,
            "front_roll_spring_force_n": front_roll_travel
            * 1000.0
            * self.vehicle.front.spring.roll_n_per_mm,
            "rear_roll_spring_force_n": rear_roll_travel
            * 1000.0
            * self.vehicle.rear.spring.roll_n_per_mm,
        }

    def _plot_longitudinal_ode(
        self,
        ax_g: float,
        filename: str,
        comparison_filename: str,
    ) -> dict[str, dict[str, np.ndarray]]:
        front_force, rear_force = self._longitudinal_transfer_forces(ax_g)
        front_dec = self._simulate_heave_axis(
            self.vehicle.front,
            self.heave.front,
            self.damper.damper_curve_for_axle(self.vehicle.front),
            front_force,
            independent=False,
        )
        rear_dec = self._simulate_heave_axis(
            self.vehicle.rear,
            self.heave.rear,
            self.damper.damper_curve_for_axle(self.vehicle.rear),
            rear_force,
            independent=False,
        )
        front_ind = self._simulate_heave_axis(
            self.vehicle.front,
            self.independent.front,
            self.damper.damper_curve_for_axle(self.vehicle.front, independent=True),
            front_force / 2.0,
            independent=True,
        )
        rear_ind = self._simulate_heave_axis(
            self.vehicle.rear,
            self.independent.rear,
            self.damper.damper_curve_for_axle(self.vehicle.rear, independent=True),
            rear_force / 2.0,
            independent=True,
        )
        t = front_dec["time_s"]
        pitch_dec = np.rad2deg(
            np.arctan2(
                front_dec["sprung_displacement_m"] - rear_dec["sprung_displacement_m"],
                self.vehicle.wheelbase_m,
            )
        )
        pitch_ind = np.rad2deg(
            np.arctan2(
                front_ind["sprung_displacement_m"] - rear_ind["sprung_displacement_m"],
                self.vehicle.wheelbase_m,
            )
        )

        fig, ax = plt.subplots(2, 1, sharex=True, figsize=(8, 6))
        ax[0].plot(t, front_dec["sprung_displacement_m"] * 1000.0, label="front")
        ax[0].plot(t, rear_dec["sprung_displacement_m"] * 1000.0, label="rear")
        ax[0].set_ylabel("sprung z [mm]")
        ax[0].grid(True)
        ax[0].legend()
        ax[1].plot(t, pitch_dec)
        ax[1].set_xlabel("time [s]")
        ax[1].set_ylabel("pitch [deg]")
        ax[1].grid(True)
        fig.suptitle(f"Longitudinal ODE response, ax = {ax_g:.2f} g")
        fig.tight_layout()
        fig.savefig(self.output_dir / filename, dpi=200)
        plt.close(fig)

        fig, axes = plt.subplots(2, 2, sharex=True, figsize=(10, 6))
        axes[0, 0].plot(t, front_dec["sprung_displacement_m"] * 1000.0, label="front")
        axes[0, 0].plot(t, rear_dec["sprung_displacement_m"] * 1000.0, label="rear")
        axes[0, 0].set_title("Decoupled sprung displacement")
        axes[0, 0].set_ylabel("z [mm]")
        axes[0, 0].grid(True)
        axes[0, 0].legend()
        axes[1, 0].plot(t, pitch_dec, color="black")
        axes[1, 0].set_title("Decoupled pitch")
        axes[1, 0].set_xlabel("time [s]")
        axes[1, 0].set_ylabel("pitch [deg]")
        axes[1, 0].grid(True)
        axes[0, 1].plot(t, front_ind["sprung_displacement_m"] * 1000.0, label="front")
        axes[0, 1].plot(t, rear_ind["sprung_displacement_m"] * 1000.0, label="rear")
        axes[0, 1].set_title("Independent sprung displacement")
        axes[0, 1].grid(True)
        axes[0, 1].legend()
        axes[1, 1].plot(t, pitch_ind, color="black")
        axes[1, 1].set_title("Independent pitch")
        axes[1, 1].set_xlabel("time [s]")
        axes[1, 1].grid(True)
        fig.suptitle(f"Non-linear simulation, ax = {ax_g:.2f} g")
        fig.tight_layout()
        fig.savefig(self.output_dir / comparison_filename, dpi=200)
        plt.close(fig)

        if ax_g < 0.0:
            front_tire = (
                self.vehicle.weight_n * self.vehicle.front.weight_ratio / 2.0
                + front_dec["tire_force_delta_n"] / 2.0
            )
            rear_tire = (
                self.vehicle.weight_n * self.vehicle.rear.weight_ratio / 2.0
                + rear_dec["tire_force_delta_n"] / 2.0
            )
            front_tire_ind = (
                self.vehicle.weight_n * self.vehicle.front.weight_ratio / 2.0
                + front_ind["tire_force_delta_n"]
            )
            rear_tire_ind = (
                self.vehicle.weight_n * self.vehicle.rear.weight_ratio / 2.0
                + rear_ind["tire_force_delta_n"]
            )
            fig, axes = plt.subplots(1, 2, figsize=(10, 4.8), sharey=True)
            axes[0].plot(t, front_tire, label="front")
            axes[0].plot(t, rear_tire, label="rear")
            axes[0].set_title("Decoupled axle model")
            axes[0].set_xlabel("time [s]")
            axes[0].set_ylabel("normal load [N]")
            axes[0].grid(True)
            axes[0].legend()
            axes[1].plot(t, front_tire_ind, label="front")
            axes[1].plot(t, rear_tire_ind, label="rear")
            axes[1].set_title("Independent model")
            axes[1].set_xlabel("time [s]")
            axes[1].grid(True)
            axes[1].legend()
            fig.suptitle(f"Braking tire Fz transient, ax = {ax_g:.2f} g")
            fig.tight_layout()
            fig.savefig(self.output_dir / "ode_braking_tire_fz.png", dpi=200)
            plt.close(fig)

        return {
            "front_decoupled": front_dec,
            "rear_decoupled": rear_dec,
            "front_independent": front_ind,
            "rear_independent": rear_ind,
            "pitch_decoupled_deg": {"time_s": t, "value": pitch_dec},
            "pitch_independent_deg": {"time_s": t, "value": pitch_ind},
        }

    def _plot_decoupled_longitudinal_comparison(
        self,
        braking: dict[str, dict[str, np.ndarray]],
        acceleration: dict[str, dict[str, np.ndarray]],
    ) -> None:
        t = braking["front_decoupled"]["time_s"]
        fig, axes = plt.subplots(2, 2, sharex=True, figsize=(10.5, 6.2))
        axes[0, 0].plot(t, braking["front_decoupled"]["sprung_displacement_m"] * 1000.0, label="front")
        axes[0, 0].plot(t, braking["rear_decoupled"]["sprung_displacement_m"] * 1000.0, label="rear")
        braking_g = self.vehicle.analysis.ode_braking_g
        acceleration_g = self.vehicle.analysis.ode_acceleration_g
        axes[0, 0].set_title(
            f"Decoupled -{braking_g:.2f} g braking sprung displacement"
        )
        axes[0, 0].set_ylabel("z [mm]")
        axes[0, 0].grid(True)
        axes[0, 0].legend()
        axes[0, 1].plot(t, acceleration["front_decoupled"]["sprung_displacement_m"] * 1000.0, label="front")
        axes[0, 1].plot(t, acceleration["rear_decoupled"]["sprung_displacement_m"] * 1000.0, label="rear")
        axes[0, 1].set_title(
            f"Decoupled {acceleration_g:.2f} g acceleration sprung displacement"
        )
        axes[0, 1].grid(True)
        axes[0, 1].legend()
        axes[1, 0].plot(t, braking["pitch_decoupled_deg"]["value"], color="black")
        axes[1, 0].set_title(f"Decoupled -{braking_g:.2f} g braking pitch")
        axes[1, 0].set_xlabel("time [s]")
        axes[1, 0].set_ylabel("pitch [deg]")
        axes[1, 0].grid(True)
        axes[1, 1].plot(t, acceleration["pitch_decoupled_deg"]["value"], color="black")
        axes[1, 1].set_title(f"Decoupled {acceleration_g:.2f} g acceleration pitch")
        axes[1, 1].set_xlabel("time [s]")
        axes[1, 1].grid(True)
        fig.suptitle("Decoupled longitudinal response: braking vs acceleration")
        fig.tight_layout()
        fig.savefig(self.output_dir / "fig_decoupled_longitudinal_accel_brake_ode45.png", dpi=200)
        plt.close(fig)

    def _longitudinal_transfer_forces(self, ax_g: float) -> tuple[float, float]:
        transfer_axis = (
            ax_g
            * self.vehicle.weight_n
            * self.vehicle.cg_height_m
            / self.vehicle.wheelbase_m
        )
        return -transfer_axis, transfer_axis

    def _simulate_heave_axis(
        self,
        axle: Axle,
        heave_result,
        damper: DamperCurve,
        external_force_n: float,
        independent: bool,
    ) -> dict[str, np.ndarray]:
        ms = axle.sprung_mass_per_wheel_kg if independent else axle.sprung_mass_axis_kg
        mu = axle.unsprung_mass_per_wheel_kg if independent else axle.unsprung_mass_axis_kg
        ks = heave_result.wheel_rate_n_per_m
        kt = self.vehicle.tire_vertical_rate_n_per_m if independent else 2.0 * self.vehicle.tire_vertical_rate_n_per_m
        mr = axle.motion_ratio.independent if independent else axle.motion_ratio.heave
        t_eval = np.linspace(0.0, 2.0, 900)

        def rhs(_t: float, x: np.ndarray) -> np.ndarray:
            z_s, v_s, z_u, v_u = x
            rel_z = z_s - z_u
            rel_v = v_s - v_u
            damper_force = damper.force(rel_v * mr * 1000.0).item() * mr
            spring_force = ks * rel_z
            dzs = v_s
            dvs = (-spring_force - damper_force + external_force_n) / ms
            dzu = v_u
            dvu = (spring_force + damper_force - kt * z_u) / mu
            return np.array([dzs, dvs, dzu, dvu])

        solution = solve_ivp(
            rhs,
            (t_eval[0], t_eval[-1]),
            np.zeros(4),
            t_eval=t_eval,
            rtol=1e-7,
            atol=1e-9,
        )
        return {
            "time_s": solution.t,
            "sprung_displacement_m": solution.y[0],
            "unsprung_displacement_m": solution.y[2],
            "tire_force_delta_n": kt * solution.y[2],
        }
