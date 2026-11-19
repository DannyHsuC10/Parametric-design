from __future__ import annotations

from dataclasses import dataclass
from math import degrees

import numpy as np
import pandas as pd
from scipy.linalg import eigh

from vehicle import Axle, Vehicle


@dataclass(frozen=True)
class AxleRollResult:
    axle: str
    spring_rate_n_per_m: float
    wheel_rate_n_per_m: float
    tire_roll_stiffness_n_m_per_rad: float
    suspension_roll_stiffness_n_m_per_rad: float
    actual_roll_stiffness_n_m_per_rad: float
    roll_stiffness_distribution: float


@dataclass(frozen=True)
class ModalRollResult:
    natural_frequencies_hz: np.ndarray
    mode_shapes: np.ndarray
    damping_matrix_low: np.ndarray
    damping_matrix_high: np.ndarray
    target_zeta_low: np.ndarray
    target_zeta_high: np.ndarray
    sprung_to_roll_axis_height_m: float


@dataclass(frozen=True)
class RollResult:
    front: AxleRollResult
    rear: AxleRollResult
    total_roll_stiffness_n_m_per_rad: float
    roll_gradient_deg_per_g: float
    modal: ModalRollResult
    mass_matrix: np.ndarray
    stiffness_matrix: np.ndarray

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                self.front.__dict__,
                self.rear.__dict__,
                {
                    "axle": "total",
                    "spring_rate_n_per_m": np.nan,
                    "wheel_rate_n_per_m": np.nan,
                    "tire_roll_stiffness_n_m_per_rad": np.nan,
                    "suspension_roll_stiffness_n_m_per_rad": np.nan,
                    "actual_roll_stiffness_n_m_per_rad": self.total_roll_stiffness_n_m_per_rad,
                    "roll_stiffness_distribution": 1.0,
                    "roll_gradient_deg_per_g": self.roll_gradient_deg_per_g,
                },
            ]
        )


class RollAnalysis:
    def __init__(self, vehicle: Vehicle):
        self.vehicle = vehicle

    def run(self) -> RollResult:
        front = self._calc_axle(self.vehicle.front)
        rear = self._calc_axle(self.vehicle.rear)
        total = front.actual_roll_stiffness_n_m_per_rad + rear.actual_roll_stiffness_n_m_per_rad

        front = AxleRollResult(
            **{
                **front.__dict__,
                "roll_stiffness_distribution": front.actual_roll_stiffness_n_m_per_rad / total,
            }
        )
        rear = AxleRollResult(
            **{
                **rear.__dict__,
                "roll_stiffness_distribution": rear.actual_roll_stiffness_n_m_per_rad / total,
            }
        )

        h_c2ra = self.sprung_to_roll_axis_height()
        roll_gradient = degrees(self.vehicle.weight_n * h_c2ra / total)
        mass, stiffness = self.roll_matrices(front, rear)
        modal = self.modal_analysis(mass, stiffness, front, rear, h_c2ra)

        return RollResult(
            front=front,
            rear=rear,
            total_roll_stiffness_n_m_per_rad=total,
            roll_gradient_deg_per_g=roll_gradient,
            modal=modal,
            mass_matrix=mass,
            stiffness_matrix=stiffness,
        )

    def sprung_to_roll_axis_height(self) -> float:
        front = self.vehicle.front
        rear = self.vehicle.rear
        roll_axis_at_cg = (
            (rear.roll_center_height_m - front.roll_center_height_m)
            * rear.weight_ratio
            + front.roll_center_height_m
        )
        return self.vehicle.cg_height_m - roll_axis_at_cg

    def _calc_axle(self, axle: Axle) -> AxleRollResult:
        wheel_rate = axle.spring.roll_n_per_m * axle.motion_ratio.roll**2
        tire_roll = self.vehicle.tire_vertical_rate_n_per_m * axle.track_m**2 / 2.0
        suspension_roll = wheel_rate * axle.track_m**2
        actual_roll = suspension_roll * tire_roll / (suspension_roll + tire_roll)

        return AxleRollResult(
            axle=axle.name,
            spring_rate_n_per_m=axle.spring.roll_n_per_m,
            wheel_rate_n_per_m=wheel_rate,
            tire_roll_stiffness_n_m_per_rad=tire_roll,
            suspension_roll_stiffness_n_m_per_rad=suspension_roll,
            actual_roll_stiffness_n_m_per_rad=actual_roll,
            roll_stiffness_distribution=0.0,
        )

    def roll_matrices(
        self, front: AxleRollResult, rear: AxleRollResult
    ) -> tuple[np.ndarray, np.ndarray]:
        kf = front.suspension_roll_stiffness_n_m_per_rad
        kr = rear.suspension_roll_stiffness_n_m_per_rad
        ktf = front.tire_roll_stiffness_n_m_per_rad
        ktr = rear.tire_roll_stiffness_n_m_per_rad

        mass = np.diag(
            [
                self.vehicle.sprung_roll_inertia_kg_m2,
                self.vehicle.front.unsprung_roll_inertia_kg_m2,
                self.vehicle.rear.unsprung_roll_inertia_kg_m2,
            ]
        )
        stiffness = np.array(
            [
                [kf + kr, -kf, -kr],
                [-kf, kf + ktf, 0.0],
                [-kr, 0.0, kr + ktr],
            ],
            dtype=float,
        )
        return mass, stiffness

    def modal_analysis(
        self,
        mass: np.ndarray,
        stiffness: np.ndarray,
        front: AxleRollResult,
        rear: AxleRollResult,
        h_c2ra: float,
    ) -> ModalRollResult:
        eigenvalues, mode_shapes = eigh(stiffness, mass)
        order = np.argsort(eigenvalues)
        eigenvalues = eigenvalues[order]
        mode_shapes = mode_shapes[:, order]
        omega = np.sqrt(np.maximum(eigenvalues, 0.0))
        frequencies = omega / (2.0 * np.pi)

        front_share = front.suspension_roll_stiffness_n_m_per_rad / (
            front.suspension_roll_stiffness_n_m_per_rad
            + rear.suspension_roll_stiffness_n_m_per_rad
        )
        rear_share = 1.0 - front_share
        zeta_low = np.full(
            3,
            front_share * self.vehicle.front.roll_damping_ratio.low
            + rear_share * self.vehicle.rear.roll_damping_ratio.low,
        )
        zeta_high = np.full(
            3,
            front_share * self.vehicle.front.roll_damping_ratio.high
            + rear_share * self.vehicle.rear.roll_damping_ratio.high,
        )

        damping_low = self._modal_damping_matrix(mass, mode_shapes, omega, zeta_low)
        damping_high = self._modal_damping_matrix(mass, mode_shapes, omega, zeta_high)
        return ModalRollResult(
            natural_frequencies_hz=frequencies,
            mode_shapes=mode_shapes,
            damping_matrix_low=damping_low,
            damping_matrix_high=damping_high,
            target_zeta_low=zeta_low,
            target_zeta_high=zeta_high,
            sprung_to_roll_axis_height_m=h_c2ra,
        )

    @staticmethod
    def _modal_damping_matrix(
        mass: np.ndarray,
        modes: np.ndarray,
        omega: np.ndarray,
        zeta: np.ndarray,
    ) -> np.ndarray:
        # scipy.linalg.eigh returns mass-normalized modes for the generalized problem.
        return mass @ modes @ np.diag(2.0 * zeta * omega) @ modes.T @ mass
