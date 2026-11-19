"""Two uncoupled, undamped load-transfer paths under a lateral step.

Roll angle is rad, chassis displacement is m, linear stiffness is N/m.
The roll force uses track * angle as its equivalent displacement.
"""

from dataclasses import dataclass

import numpy as np

G = 9.81


@dataclass(frozen=True)
class Axle:
    mass: float
    inertia: float
    track: float
    height: float
    spring_rate: float
    chassis_rate: float

    @property
    def roll_frequency(self):
        return np.sqrt(self.spring_rate * self.track**2 / self.inertia)

    @property
    def chassis_frequency(self):
        return np.sqrt(self.chassis_rate / (self.mass / 4))


def validate(p):
    nonnegative = {"ay", "rc_sweep_min_ratio", "rc_front_min_peak_rate_N_per_s", "rc_front_optimal_height_m"}
    for name, value in p.items():
        if not np.isfinite(value):
            raise ValueError(f"{name} 必須是有限數值")
        if value < 0 or (value == 0 and name not in nonnegative):
            raise ValueError(f"{name} 必須{'不小於' if name in nonnegative else '大於'}零")
    if "hl_sprung_front_weight_ratio" in p and not 0 < p["hl_sprung_front_weight_ratio"] < 1:
        raise ValueError("簧上前軸配重必須介於 0 與 1 之間")
    if "rc_sweep_points" in p:
        count = p["rc_sweep_points"]
        if int(count) != count or not 3 <= count <= 501:
            raise ValueError("Roll Center 掃描點數必須為 3～501 的整數")
        if not 0 <= p["rc_sweep_min_ratio"] < p["rc_sweep_max_ratio"] <= 1:
            raise ValueError("Roll Center 掃描範圍須符合 0 ≤ 下限 < 上限 ≤ 1")
        if p["rc_time_step_s"] >= p["rc_simulation_duration_s"]:
            raise ValueError("取樣間隔必須小於模擬時間")
        if p["rc_simulation_duration_s"] / p["rc_time_step_s"] > 200000:
            raise ValueError("時間取樣超過 200000 點，請增加取樣間隔或縮短模擬時間")
    for name in ("rc_front_optimal_height_m",):
        if name in p and p[name] > p["h_cog"]:
            raise ValueError(f"{name} 在此模型中不可高於重心高度 h_cog")


def make_axle(p, rear=False):
    share = p["hl_sprung_front_weight_ratio"]
    if rear:
        share = 1 - share
    name = "rear" if rear else "front"
    track = p["hl_rear_track_m"] if rear else p["t"]
    spring_rate = p["Ks_roll_N_per_m"] * p[f"hl_{name}_roll_motion_ratio"]**2
    if rear:
        spring_rate *= p["hl_rear_roll_spring_ratio"]
    return Axle(p["ms"] * share, p["cog_total_Ixx_kg_m2"] / 2,
                track, p["h_cog"], spring_rate, spring_rate * p["rc_chassis_stiffness_ratio"])


def time_grid(p, *axles):
    duration, step = p["rc_simulation_duration_s"], p["rc_time_step_s"]
    characteristic = []
    for axle in axles:
        for frequency in (axle.roll_frequency, axle.chassis_frequency):
            end = np.pi / frequency
            if duration < end:
                raise ValueError(f"模擬時間不足以涵蓋首次脈衝，請設定至少 {end:.4f} s")
            # Resolve each half-sine pulse even if the user's time step is coarse.
            characteristic.extend(np.linspace(0, end, 201))
    grid = np.arange(0, duration, step)
    return np.unique(np.r_[grid, duration, characteristic])


def pulse_basis(axle, times):
    basis = []
    for frequency in (axle.roll_frequency, axle.chassis_frequency):
        active = times <= np.pi / frequency
        basis.append(np.where(active, np.maximum(0, frequency * np.sin(frequency * times)), 0))
    return basis


def amplitudes(axle, rc_height, acceleration):
    if not np.isfinite(rc_height) or not 0 <= rc_height <= axle.height:
        raise ValueError("Roll Center 高度必須位於地面與重心之間")
    return (-acceleration * axle.mass * (axle.height - rc_height) / axle.track,
            -acceleration * axle.mass * rc_height / axle.track)


def response(axle, rc_height, acceleration, times):
    spring_eq, chassis_eq = amplitudes(axle, rc_height, acceleration)
    spring_basis, chassis_basis = pulse_basis(axle, times)
    spring = spring_eq * (1 - np.cos(axle.roll_frequency * times))
    chassis = chassis_eq * (1 - np.cos(axle.chassis_frequency * times))
    spring_rate, chassis_rate = spring_eq * spring_basis, chassis_eq * chassis_basis
    total_rate = spring_rate + chassis_rate
    peak_index = int(np.argmax(np.abs(total_rate)))
    return {"time_s": times, "suspension_transfer_N": spring, "chassis_transfer_N": chassis,
            "total_transfer_N": spring + chassis,
            "suspension_first_pulse_rate_N_per_s": spring_rate,
            "chassis_first_pulse_rate_N_per_s": chassis_rate,
            "total_first_pulse_rate_N_per_s": total_rate,
            "peak_rate_N_per_s": float(abs(total_rate[peak_index])),
            "peak_time_s": float(times[peak_index])}


def sweep(axle, ratios, acceleration, times):
    spring_basis, chassis_basis = pulse_basis(axle, times)
    total = -acceleration * axle.mass * axle.height / axle.track
    return np.asarray([np.max(np.abs(total * ((1 - ratio) * spring_basis + ratio * chassis_basis)))
                       for ratio in ratios])
