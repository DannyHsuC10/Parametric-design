import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")

OUTPUT_DIR = Path(__file__).parent
OUTPUT_DIR.mkdir(exist_ok=True)
# ============================================================
# Parameters
# ============================================================

g = 9.81

# Vehicle
m = param.m                  # Vehicle mass [kg]

l = param.L                   # Wheelbase [m]
l_f = param.lf                # CG to front axle [m]
l_r = l - l_f              # CG to rear axle [m]

h_cog = param.h_cog              # CG height [m]

# Tire
r_w = param.rw                # Wheel radius [m]

mu_w = min(param.a_acc,param.mu_w)
# Target
target_v = param.target_v          # [km/h]
a_max = mu_w * g

# Motor
T_motor_max = param.T_motor        # Maximum motor torque [Nm]
RPM_motor_max = param.RPM_motor    # Maximum motor RPM


# ============================================================
# Static normal force
# ============================================================

N_r_static = m * g * l_f / l
N_f_static = m * g - N_r_static

print(
    f"Rear static load  : {N_r_static:.2f} N"
)

print(
    f"Front static load : {N_f_static:.2f} N"
)


# ============================================================
# Target acceleration
# Tire traction limit
# ============================================================



print(
    f"\nMaximum acceleration : "
    f"{a_max:.2f} m/s² "
    f"({a_max / g:.2f} g)"
)


# ============================================================
# Dynamic normal force
# Maximum acceleration load transfer
# ============================================================

F_x_total = m * a_max

N_r = (
    F_x_total * h_cog
    + m * g * l_f
) / l

delta_N = N_r - N_r_static

N_f = N_f_static - delta_N


print(
    f"\nRear dynamic load : {N_r:.2f} N"
)

print(
    f"Front dynamic load: {N_f:.2f} N"
)


# ============================================================
# Maximum tire traction force
# ============================================================

F_xf = mu_w * N_f
F_xr = mu_w * N_r

error = F_xf + F_xr - F_x_total


print(
    f"\nFront traction limit : {F_xf:.2f} N"
)

print(
    f"Rear traction limit  : {F_xr:.2f} N"
)

print(
    f"Error                : {error:.2f} N"
)


# ============================================================
# Wheel torque requirement
# ============================================================

M_ar = F_xr * r_w
M_af = F_xf * r_w


print(
    f"\nFront moment limit : {M_af:.2f} Nm"
)

print(
    f"Rear moment limit  : {M_ar:.2f} Nm"
)


M_a = max(
    M_ar,
    M_af
)


print(
    f"Max moment         : {M_a:.2f} Nm"
)


# ============================================================
# Motor torque and gear ratio
# ============================================================

# Assume left/right wheels share torque equally
M_w = M_a / 2.0

Z_a = M_w / T_motor_max


print(
    f"\nWheel torque required : {M_w:.2f} Nm"
)

print(
    f"Gear ratio (accel)    : {Z_a:.2f}"
)


# ============================================================
# Top speed gear ratio
# ============================================================

# km/h -> m/s
target_v_ms = target_v / 3.6


# Wheel angular velocity
omega_w_max = target_v_ms / r_w


# rad/s -> RPM
RPM_w = omega_w_max * 60.0 / (2.0 * np.pi)


# Gear ratio
Z_ts = RPM_motor_max / RPM_w


print(
    f"\nWheel RPM @ top speed : "
    f"{RPM_w:.2f} RPM"
)

print(
    f"Gear ratio (top speed): "
    f"{Z_ts:.2f}"
)


# ============================================================
# Average gear ratio
# ============================================================

Z_avg = (Z_ts + Z_a) / 2.0


print(
    f"\nGear ratio (avg): {Z_avg:.2f}"
)

# =========================================================
# Motor RPM vs Vehicle Speed
# =========================================================

# Vehicle speed range
v_max_plot = target_v/3.6 * 1.1
v_array = np.linspace(0, v_max_plot, 150)

# Convert vehicle speed -> wheel RPM
rpm_wheel = v_array / r_w * 60 / (2 * np.pi)

# Motor RPM for each gear ratio
rpm_motor_a = rpm_wheel * Z_a
rpm_motor_ts = rpm_wheel * Z_ts
rpm_motor_avg = rpm_wheel * Z_avg

# =========================================================
# Plot
# =========================================================

plt.figure(figsize=(8, 6))

plt.plot(
    v_array * 3.6,
    rpm_motor_a,
    linewidth=2,
    label=f"Z_a = {Z_a:.2f}"
)

plt.plot(
    v_array * 3.6,
    rpm_motor_ts,
    linewidth=2,
    label=f"Z_ts = {Z_ts:.2f}"
)

plt.plot(
    v_array * 3.6,
    rpm_motor_avg,
    linewidth=2,
    label=f"Z_avg = {Z_avg:.2f}"
)

# Motor maximum RPM
plt.axhline(
    RPM_motor_max,
    linestyle="--",
    linewidth=1.5,
    label=f"Motor Max RPM = {RPM_motor_max:.0f}"
)

# Target vehicle speed
plt.axvline(
    target_v ,
    linestyle="--",
    linewidth=1.5,
    label=f"Target Speed = {target_v:.1f} km/h"
)

plt.xlabel("Vehicle Speed (km/h)")
plt.ylabel("Motor Speed (RPM)")
plt.title("Motor Speed vs Vehicle Speed")

plt.grid(True)
plt.legend()
plt.tight_layout()

output_path = OUTPUT_DIR / "Motor_Vehicle_speed.png"

plt.savefig(
    output_path,
    dpi=300,
    bbox_inches="tight"
)


plt.show()

