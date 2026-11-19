"""Linear bicycle step response using shared mass/inertia and a manual reference speed."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis.cornering.models import bicycle_step_response, require_positive
from app.analysis_result import AnalysisResult

TITLE = "Bicycle_Model"
DESCRIPTION = "Linear two-state bicycle-model response to a steering step."
PLUGIN_ID = "bicycle_model"
STEERING_STEP_TIME_S = 0.5
SIMULATION_DURATION_S = 5.0
NUM_POINTS_BICYCLE = 1000
PARAMETER_DEFAULTS = {
    "bicycle_front_cornering_stiffness_N_per_rad": 40000.0,
    "bicycle_rear_cornering_stiffness_N_per_rad": 40000.0,
    "bicycle_v_ref_kmh": 40.0,
}
PARAMETERS = dict.fromkeys(("cog_total_mass_kg", "cog_total_Izz_kg_m2", "L",
                            "hl_front_weight_ratio", "vehicle_max_steering_angle_deg",
                            *PARAMETER_DEFAULTS), "float")
HIDDEN_PARAMETERS = {"cog_total_mass_kg", "cog_total_Izz_kg_m2"}
OUTPUTS = {
    "bicycle_final_yaw_rate_deg_per_s": "Yaw rate at the final simulation time (deg/s)",
    "bicycle_final_lateral_velocity_mps": "Lateral velocity at the final simulation time (m/s)",
    "bicycle_final_front_slip_deg": "Front tire slip angle at the final simulation time (deg)",
    "bicycle_final_rear_slip_deg": "Rear tire slip angle at the final simulation time (deg)",
    "bicycle_front_cg_distance_m": "Distance from total CG to the front axle (m)",
    "bicycle_rear_cg_distance_m": "Distance from total CG to the rear axle (m)",
}


def main(parameters):
    values = PARAMETER_DEFAULTS | parameters
    require_positive(values, ("cog_total_mass_kg", "cog_total_Izz_kg_m2", "L", "bicycle_v_ref_kmh",
                     "bicycle_front_cornering_stiffness_N_per_rad",
                     "bicycle_rear_cornering_stiffness_N_per_rad"))
    ratio = values["hl_front_weight_ratio"]
    step_time, duration = STEERING_STEP_TIME_S, SIMULATION_DURATION_S
    steering = values["vehicle_max_steering_angle_deg"]
    count = NUM_POINTS_BICYCLE
    if not np.isfinite(ratio) or not 0 < ratio < 1:
        raise ValueError("Front weight ratio must be strictly between zero and one")
    if not np.isfinite(steering) or not 0 < steering < 90:
        raise ValueError("Vehicle maximum steering angle must be between 0 and 90 degrees")
    vx = values["bicycle_v_ref_kmh"] / 3.6
    mass, inertia = values["cog_total_mass_kg"], values["cog_total_Izz_kg_m2"]
    # Static front weight fraction = lr / L.
    lf, lr = values["L"] * (1 - ratio), values["L"] * ratio
    cf, cr = (values["bicycle_front_cornering_stiffness_N_per_rad"],
              values["bicycle_rear_cornering_stiffness_N_per_rad"])
    times = np.linspace(0, duration, int(count))
    delta = np.deg2rad(steering) * (times > step_time)
    vy, yaw_rate = bicycle_step_response(times, step_time, np.deg2rad(steering),
                                         vx, mass, inertia, lf, lr, cf, cr)
    front_slip = delta - (vy + lf * yaw_rate) / vx
    rear_slip = -(vy - lr * yaw_rate) / vx
    figure, axes = plt.subplots(3, 1, figsize=(8, 8), sharex=True)
    axes[0].plot(times, np.rad2deg(yaw_rate), linewidth=2)
    axes[0].set_ylabel("Yaw Rate (deg/s)")
    axes[1].plot(times, vy, linewidth=2)
    axes[1].set_ylabel("Lateral Velocity (m/s)")
    axes[2].plot(times, np.rad2deg(front_slip), linewidth=2, label="Front slip")
    axes[2].plot(times, np.rad2deg(rear_slip), linewidth=2, label="Rear slip")
    axes[2].set(xlabel="Time (s)", ylabel="Slip Angle (deg)")
    axes[2].legend()
    for axis in axes:
        axis.grid(True)
    figure.suptitle("Linear Bicycle Model Response")
    figure.tight_layout()
    outputs = {
        "bicycle_final_yaw_rate_deg_per_s": float(np.rad2deg(yaw_rate[-1])),
        "bicycle_final_lateral_velocity_mps": float(vy[-1]),
        "bicycle_final_front_slip_deg": float(np.rad2deg(front_slip[-1])),
        "bicycle_final_rear_slip_deg": float(np.rad2deg(rear_slip[-1])),
        "bicycle_front_cg_distance_m": float(lf), "bicycle_rear_cg_distance_m": float(lr),
    }
    print(f"Bicycle model: m={mass:.3f} kg, Iz={inertia:.3f} kg m², speed={vx:.3f} m/s")
    print(f"Final yaw rate: {outputs['bicycle_final_yaw_rate_deg_per_s']:.3f} deg/s")
    return AnalysisResult(figure, outputs,
                          tables={"bicycle_response.csv": pd.DataFrame({"time_s": times,
                                  "steering_deg": np.rad2deg(delta), "lateral_velocity_mps": vy,
                                  "yaw_rate_rad_per_s": yaw_rate, "yaw_rate_deg_per_s": np.rad2deg(yaw_rate),
                                  "front_slip_deg": np.rad2deg(front_slip), "rear_slip_deg": np.rad2deg(rear_slip)})},
                          figure_titles={"plot.png": "Bicycle Model 偏航、側向速度與側滑角"})
