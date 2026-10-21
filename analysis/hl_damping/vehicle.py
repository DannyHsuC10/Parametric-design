from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import math

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


def make_vehicle(parameters) -> Vehicle:
    """Build from the toolbox CSV; spring rates are upstream axle spring rates."""
    p = parameters
    for name, value in p.items():
        if not math.isfinite(value):
            raise ValueError(f"{name} 必須是有限數值")
    positive = (
        "ms", "mu", "MR", "Kt", "L", "t",
        "hl_rear_track_m", "hl_sprung_roll_inertia_kg_m2", "Ks_pitch_N_per_m",
        "Ks_roll_N_per_m", "hl_rear_heave_spring_ratio", "hl_rear_roll_spring_ratio",
        "hl_front_roll_motion_ratio", "hl_rear_roll_motion_ratio",
        "hl_front_independent_motion_ratio", "hl_rear_independent_motion_ratio",
        "hl_knee_velocity_mm_s", "h_cog",
    )
    for name in positive:
        if p[name] <= 0:
            raise ValueError(f"{name} 必須大於零")
    if not 0 < p["hl_front_weight_ratio"] < 1:
        raise ValueError("hl_front_weight_ratio 必須介於 0 和 1 之間")
    for name in p:
        if name.endswith("_zeta") or name in {"ax", "ay", "hl_acceleration_g", "hl_reference_case_g"}:
            if p[name] < 0:
                raise ValueError(f"{name} 不可為負數")

    sprung = p["ms"]
    unsprung = p["mu"]
    axles = []
    for name, weight_ratio, heave_scale, roll_scale, track in (
        ("front", p["hl_front_weight_ratio"], 1.0, 1.0, p["t"]),
        ("rear", 1.0 - p["hl_front_weight_ratio"], p["hl_rear_heave_spring_ratio"],
         p["hl_rear_roll_spring_ratio"], p["hl_rear_track_m"]),
    ):
        axles.append(Axle(
            name=name, weight_ratio=weight_ratio, track_m=track,
            roll_center_height_m=p[f"hl_{name}_roll_center_m"],
            sprung_mass_per_wheel_kg=sprung * weight_ratio / 2,
            unsprung_mass_per_wheel_kg=unsprung,
            motion_ratio=MotionRatio(p["MR"], p[f"hl_{name}_roll_motion_ratio"],
                                     p[f"hl_{name}_independent_motion_ratio"]),
            spring=SpringRate(p["Ks_pitch_N_per_m"] * heave_scale / 1000,
                              p["Ks_roll_N_per_m"] * roll_scale / 1000),
            heave_damping_ratio=HeaveDampingRatio(*(
                p[f"hl_{name}_heave_{region}_{direction}_zeta"]
                for region, direction in (("low", "bump"), ("low", "rebound"),
                                          ("high", "bump"), ("high", "rebound"))
            )),
            roll_damping_ratio=RollDampingRatio(p[f"hl_{name}_roll_low_zeta"],
                                                p[f"hl_{name}_roll_high_zeta"]),
        ))
    return Vehicle(
        mass_kg=sprung + 4 * unsprung, sprung_mass_kg=sprung,
        wheelbase_m=p["L"], cg_height_m=p["h_cog"],
        sprung_roll_inertia_kg_m2=p["hl_sprung_roll_inertia_kg_m2"],
        tire_vertical_rate_n_per_m=p["Kt"], gravity_mps2=9.80665,
        front=axles[0], rear=axles[1],
        analysis=AnalysisSettings(
            acceleration_cases_g=(p["hl_reference_case_g"], p["hl_acceleration_g"]),
            braking_cases_g=(p["hl_reference_case_g"], p["ax"]),
            cornering_cases_g=(p["hl_reference_case_g"], p["ay"]),
            ode_acceleration_g=p["hl_acceleration_g"], ode_braking_g=p["ax"],
            roll_unit_step_ay_g=p["hl_reference_case_g"], roll_step_ay_g=p["ay"],
            damper_knee_velocity_mm_s=p["hl_knee_velocity_mm_s"],
        ),
        output_dir=Path(__file__).resolve().parents[2] / "data" / "results",
    )


