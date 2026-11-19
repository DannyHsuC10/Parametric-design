from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from heave_analysis import HeaveResult
from roll_analysis import RollResult
from vehicle import Axle, Vehicle


@dataclass(frozen=True)
class IndependentAxleResult:
    axle: str
    wheel_rate_n_per_m: float
    spring_rate_n_per_m: float
    spring_rate_n_per_mm: float
    base_roll_stiffness_n_m_per_rad: float
    required_arb_stiffness_n_m_per_rad: float
    shock_low_speed_damping_n_s_per_m: float
    shock_high_speed_damping_n_s_per_m: float


@dataclass(frozen=True)
class IndependentResult:
    front: IndependentAxleResult
    rear: IndependentAxleResult

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame([self.front.__dict__, self.rear.__dict__])


class EquivalentIndependentAnalysis:
    def __init__(self, vehicle: Vehicle, heave: HeaveResult, roll: RollResult):
        self.vehicle = vehicle
        self.heave = heave
        self.roll = roll

    def run(self) -> IndependentResult:
        return IndependentResult(
            front=self._calc_axle(self.vehicle.front, self.heave.front, self.roll.front),
            rear=self._calc_axle(self.vehicle.rear, self.heave.rear, self.roll.rear),
        )

    def _calc_axle(self, axle: Axle, heave_axle, roll_axle) -> IndependentAxleResult:
        wheel_rate = heave_axle.wheel_rate_n_per_m / 2.0
        spring_rate = wheel_rate / axle.motion_ratio.independent**2
        base_roll = 0.5 * wheel_rate * axle.track_m**2
        required_arb = (
            roll_axle.suspension_roll_stiffness_n_m_per_rad - base_roll
        )
        damping_scale = axle.motion_ratio.independent**2

        return IndependentAxleResult(
            axle=axle.name,
            wheel_rate_n_per_m=wheel_rate,
            spring_rate_n_per_m=spring_rate,
            spring_rate_n_per_mm=spring_rate / 1000.0,
            base_roll_stiffness_n_m_per_rad=base_roll,
            required_arb_stiffness_n_m_per_rad=required_arb,
            shock_low_speed_damping_n_s_per_m=heave_axle.low_speed_damping_n_s_per_m
            / 2.0
            / damping_scale,
            shock_high_speed_damping_n_s_per_m=heave_axle.high_speed_damping_n_s_per_m
            / 2.0
            / damping_scale,
        )
