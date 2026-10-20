from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))# 上層資料夾即可

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")

@dataclass(frozen=True)
class HeaveDampingRatio:
    low_bump: float
    low_rebound: float
    high_bump: float
    high_rebound: float

    @property
    def low_average(self) -> float:
        return 0.5 * (self.low_bump + self.low_rebound)

    @property
    def high_average(self) -> float:
        return 0.5 * (self.high_bump + self.high_rebound)


@dataclass(frozen=True)
class RollDampingRatio:
    low: float
    high: float


@dataclass(frozen=True)
class MotionRatio:
    heave: float
    roll: float
    independent: float


@dataclass(frozen=True)
class SpringRate:
    heave_n_per_mm: float
    roll_n_per_mm: float

    @property
    def heave_n_per_m(self) -> float:
        return self.heave_n_per_mm * 1000.0

    @property
    def roll_n_per_m(self) -> float:
        return self.roll_n_per_mm * 1000.0


@dataclass(frozen=True)
class ScenarioSetting:
    name: str
    ax_g: float = 0.0
    ay_g: float = 0.0


@dataclass(frozen=True)
class AnalysisSettings:
    acceleration_cases_g: tuple[float, ...]
    braking_cases_g: tuple[float, ...]
    cornering_cases_g: tuple[float, ...]
    ode_acceleration_g: float
    ode_braking_g: float
    roll_unit_step_ay_g: float
    roll_step_ay_g: float
    damper_knee_velocity_mm_s: float

    @property
    def scenarios(self) -> tuple[ScenarioSetting, ...]:
        return (
            (ScenarioSetting("static"),)
            + tuple(
                ScenarioSetting(f"acceleration_{format_g_tag(g_value)}g", ax_g=g_value)
                for g_value in self.acceleration_cases_g
            )
            + tuple(
                ScenarioSetting(f"braking_{format_g_tag(g_value)}g", ax_g=-g_value)
                for g_value in self.braking_cases_g
            )
            + tuple(
                ScenarioSetting(f"cornering_{format_g_tag(g_value)}g", ay_g=g_value)
                for g_value in self.cornering_cases_g
            )
        )


def format_g_tag(value: float) -> str:
    return f"{value:.1f}".replace(".", "p")


@dataclass(frozen=True)
class Axle:
    name: str
    weight_ratio: float
    track_m: float
    roll_center_height_m: float
    sprung_mass_per_wheel_kg: float
    unsprung_mass_per_wheel_kg: float
    motion_ratio: MotionRatio
    spring: SpringRate
    heave_damping_ratio: HeaveDampingRatio
    roll_damping_ratio: RollDampingRatio

    @property
    def sprung_mass_axis_kg(self) -> float:
        return 2.0 * self.sprung_mass_per_wheel_kg

    @property
    def unsprung_mass_axis_kg(self) -> float:
        return 2.0 * self.unsprung_mass_per_wheel_kg

    @property
    def unsprung_roll_inertia_kg_m2(self) -> float:
        return self.unsprung_mass_per_wheel_kg * self.track_m**2 / 2.0


@dataclass(frozen=True)
class Vehicle:
    mass_kg: float
    sprung_mass_kg: float
    wheelbase_m: float
    cg_height_m: float
    sprung_roll_inertia_kg_m2: float
    tire_vertical_rate_n_per_m: float
    gravity_mps2: float
    front: Axle
    rear: Axle
    analysis: AnalysisSettings
    output_dir: Path

    @property
    def weight_n(self) -> float:
        return self.mass_kg * self.gravity_mps2

    @property
    def rear_weight_ratio(self) -> float:
        return self.rear.weight_ratio


def make_default_vehicle() -> Vehicle:# 車輛參數設定
    g = 9.80665
    mass_kg = param.m
    sprung_mass_kg = param.ms
    front_weight_ratio = param.lf/param.L
    rear_weight_ratio = 1.0 - front_weight_ratio
    wheelbase_m = param.L
    track_f_m = param.tf
    track_r_m = param.tr
    cg_height_m = param.h_cog
    unsprung_mass_per_wheel_kg = param.mu
    tire_vertical_rate_n_per_m = param.Kt

    front = Axle(# damping ratio 都先採用預設值
        name="front",
        weight_ratio=front_weight_ratio,
        track_m=track_f_m,
        roll_center_height_m=param.h_rcf,
        sprung_mass_per_wheel_kg=sprung_mass_kg * front_weight_ratio / 2.0,
        unsprung_mass_per_wheel_kg=unsprung_mass_per_wheel_kg,
        motion_ratio=MotionRatio(heave=param.MR, roll=param.MR, independent=param.MR),
        spring=SpringRate(heave_n_per_mm=param.K_heave_main/1000, roll_n_per_mm=param.K_roll_f/1000),
        heave_damping_ratio=HeaveDampingRatio(
            low_bump=0.9,
            low_rebound=0.9,
            high_bump=0.35,
            high_rebound=0.4,
        ),
        roll_damping_ratio=RollDampingRatio(low=1.0, high=0.5),
    )

    rear = Axle(
        name="rear",
        weight_ratio=rear_weight_ratio,
        track_m=track_r_m,
        roll_center_height_m=param.h_rcr,
        sprung_mass_per_wheel_kg=sprung_mass_kg * rear_weight_ratio / 2.0,
        unsprung_mass_per_wheel_kg=unsprung_mass_per_wheel_kg,
        motion_ratio=MotionRatio(heave=param.MR, roll=param.MR, independent=param.MR),
        spring=SpringRate(heave_n_per_mm=param.K_heave_main*0.8/1000, roll_n_per_mm=param.K_roll_r/1000),
        heave_damping_ratio=HeaveDampingRatio(
            low_bump=1.0,
            low_rebound=0.9,
            high_bump=0.35,
            high_rebound=0.4,
        ),
        roll_damping_ratio=RollDampingRatio(low=1.0, high=0.5),
    )

    return Vehicle(# 模擬參數設定
        mass_kg=mass_kg,
        sprung_mass_kg=sprung_mass_kg,
        wheelbase_m=wheelbase_m,
        cg_height_m=cg_height_m,
        sprung_roll_inertia_kg_m2=param.Ixu,
        tire_vertical_rate_n_per_m=tire_vertical_rate_n_per_m,
        gravity_mps2=g,
        front=front,
        rear=rear,
        analysis=AnalysisSettings(
            acceleration_cases_g=(param.a_accw, param.a_acc),
            braking_cases_g=(param.a_accw, param.ax),
            cornering_cases_g=(param.a_corner_wl, param.a_corner_wh),
            ode_acceleration_g=param.a_acc,
            ode_braking_g=param.ax,
            roll_unit_step_ay_g=param.a_corner_wl,
            roll_step_ay_g=param.a_corner_wh,
            damper_knee_velocity_mm_s=50.0,
        ),
        output_dir=Path(__file__).resolve().parent / "outputs",
    )

# 原始設定
# ==================================================
"""
g = 9.80665
mass_kg = 382.2
sprung_mass_kg = 302.3
front_weight_ratio = 0.486908
rear_weight_ratio = 1.0 - front_weight_ratio
wheelbase_m = 1.550
track_f_m = 1.250
track_r_m = 1.250
cg_height_m = 0.30546
unsprung_mass_per_wheel_kg = 19.975
tire_vertical_rate_n_per_m = 119700.0

front = Axle(
    name="front",
    weight_ratio=front_weight_ratio,
    track_m=track_f_m,
    roll_center_height_m=0.025,
    sprung_mass_per_wheel_kg=sprung_mass_kg * front_weight_ratio / 2.0,
    unsprung_mass_per_wheel_kg=unsprung_mass_per_wheel_kg,
    motion_ratio=MotionRatio(heave=0.96, roll=0.70, independent=0.48),
    spring=SpringRate(heave_n_per_mm=70.0, roll_n_per_mm=70.0),
    heave_damping_ratio=HeaveDampingRatio(
        low_bump=0.9,
        low_rebound=0.9,
        high_bump=0.35,
        high_rebound=0.4,
    ),
    roll_damping_ratio=RollDampingRatio(low=1.0, high=0.5),
)

rear = Axle(
    name="rear",
    weight_ratio=rear_weight_ratio,
    track_m=track_r_m,
    roll_center_height_m=0.050,
    sprung_mass_per_wheel_kg=sprung_mass_kg * rear_weight_ratio / 2.0,
    unsprung_mass_per_wheel_kg=unsprung_mass_per_wheel_kg,
    motion_ratio=MotionRatio(heave=0.96, roll=0.70, independent=0.48),
    spring=SpringRate(heave_n_per_mm=61.3, roll_n_per_mm=52.5),
    heave_damping_ratio=HeaveDampingRatio(
        low_bump=1.0,
        low_rebound=0.9,
        high_bump=0.35,
        high_rebound=0.4,
    ),
    roll_damping_ratio=RollDampingRatio(low=1.0, high=0.5),
)

analysis=AnalysisSettings(
    acceleration_cases_g=(1.0, 1.2),
    braking_cases_g=(1.0, 1.6),
    cornering_cases_g=(1.0, 1.6),
    ode_acceleration_g=1.2,
    ode_braking_g=1.6,
    roll_unit_step_ay_g=1.0,
    roll_step_ay_g=1.6,
    damper_knee_velocity_mm_s=50.0,
),

"""