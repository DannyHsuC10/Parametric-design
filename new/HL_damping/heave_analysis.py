from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt

import pandas as pd

from vehicle import Axle, Vehicle


@dataclass(frozen=True)
class AxleHeaveResult:
    axle: str
    spring_rate_n_per_m: float
    wheel_rate_n_per_m: float
    ride_rate_n_per_m: float
    natural_frequency_hz: float
    critical_damping_n_s_per_m: float
    low_speed_damping_n_s_per_m: float
    high_speed_damping_n_s_per_m: float


@dataclass(frozen=True)
class HeaveResult:
    front: AxleHeaveResult
    rear: AxleHeaveResult

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame([self.front.__dict__, self.rear.__dict__])


class HeaveAnalysis:
    def __init__(self, vehicle: Vehicle):
        self.vehicle = vehicle

    def run(self) -> HeaveResult:
        return HeaveResult(
            front=self._calc_axle(self.vehicle.front),
            rear=self._calc_axle(self.vehicle.rear),
        )

    def _calc_axle(self, axle: Axle) -> AxleHeaveResult:
        wheel_rate = axle.spring.heave_n_per_m * axle.motion_ratio.heave**2
        tire_axis_rate = 2.0 * self.vehicle.tire_vertical_rate_n_per_m
        ride_rate = wheel_rate * tire_axis_rate / (wheel_rate + tire_axis_rate)
        natural_frequency = sqrt(ride_rate / axle.sprung_mass_axis_kg) / (2.0 * pi)
        critical_damping = 2.0 * sqrt(wheel_rate * axle.sprung_mass_axis_kg)

        return AxleHeaveResult(
            axle=axle.name,
            spring_rate_n_per_m=axle.spring.heave_n_per_m,
            wheel_rate_n_per_m=wheel_rate,
            ride_rate_n_per_m=ride_rate,
            natural_frequency_hz=natural_frequency,
            critical_damping_n_s_per_m=critical_damping,
            low_speed_damping_n_s_per_m=critical_damping
            * axle.heave_damping_ratio.low_average,
            high_speed_damping_n_s_per_m=critical_damping
            * axle.heave_damping_ratio.high_average,
        )
