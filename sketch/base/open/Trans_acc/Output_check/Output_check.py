import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")


# =========================================================
# Output path
# =========================================================

OUTPUT_DIR = Path(__file__).resolve().parent

plot_path = OUTPUT_DIR / "acceleration_simulation.png"


# =========================================================
# Parameters
# =========================================================

g = 9.81

# -------- Gear parameters --------
Ts = param.Ts          # Sun gear teeth
Tp1 = param.Tp1         # Planet gear 1 teeth
Tr = param.Tr          # Ring gear teeth
Tp2 = param.Tp2         # Planet gear 2 teeth

M = param.M_gear          # Gear module [mm]

# -------- Motor --------
T_motor_max = param.T_motor       # Motor maximum torque [Nm]
RPM_motor_max = param.RPM_motor     # Motor maximum RPM

# -------- Vehicle --------
m = param.m                    # Vehicle mass [kg]

mu_w = param.mu_w                # Tire friction coefficient

r_w = param.rw                # Wheel radius [m]

h_cog = param.h_cog             # CG height [m]

l = param.L                   # Wheelbase [m]
l_f = param.lf                # CG to front axle [m]


# =========================================================
# Gear Ratio
# =========================================================

z = (Tp1 / Ts) * (Tr / Tp2)

print("==============================")
print("Gear / Vehicle Verification")
print("==============================")

print(f"Gear ratio: {z:.2f}")


# =========================================================
# Output torque
# =========================================================

T_out = T_motor_max * z

print(f"Output torque: {T_out:.2f} Nm")


# =========================================================
# Maximum speed
# =========================================================

RPM_out = RPM_motor_max / z

v_max = (
    np.pi
    * r_w
    * 2
    * RPM_out
    * 60
    / 1000
)

print(f"Maximum speed: {v_max/3.6:.2f} km/h")


# =========================================================
# Maximum axle force
# =========================================================

F_motor = T_out / r_w

F_axle = F_motor * 2

print(f"Maximum axle force: {F_axle:.2f} N")


# =========================================================
# Acceleration simulation parameters
# =========================================================

a = 0.0
v = 0.0
x = 0.0

t_max = 10.0
dt = 0.1

N = int(t_max / dt)

a_list = np.zeros(N)
v_list = np.zeros(N)
x_list = np.zeros(N)
t_list = np.zeros(N)


# =========================================================
# Acceleration simulation
# =========================================================

for i in range(N):

    # -----------------------------------------------------
    # Total longitudinal force
    # -----------------------------------------------------

    F_x_total = m * a


    # -----------------------------------------------------
    # Dynamic normal load
    # -----------------------------------------------------

    N_r = (
        F_x_total * h_cog
        + m * g * l_f
    ) / l

    N_f = m * g - N_r


    # -----------------------------------------------------
    # Maximum motor output force
    # -----------------------------------------------------

    Ff = F_axle
    Fr = F_axle


    # -----------------------------------------------------
    # Tire traction limit
    # -----------------------------------------------------

    if F_axle > N_r * mu_w:
        Fr = N_r * mu_w

    if F_axle > N_f * mu_w:
        Ff = N_f * mu_w


    # -----------------------------------------------------
    # Total available longitudinal force
    # -----------------------------------------------------

    F = Ff + Fr


    # -----------------------------------------------------
    # Vehicle acceleration
    # -----------------------------------------------------

    a = F / m


    # -----------------------------------------------------
    # Velocity integration
    # -----------------------------------------------------

    v = v + a * dt

    # Limit by maximum speed
    v = min(v, v_max / 3.6)


    # -----------------------------------------------------
    # Position integration
    # -----------------------------------------------------

    x = x + v * dt


    # -----------------------------------------------------
    # Store results
    # -----------------------------------------------------

    a_list[i] = a / g
    v_list[i] = v * 3.6
    x_list[i] = x
    t_list[i] = (i + 1) * dt


# =========================================================
# Final results
# =========================================================

print()
print("==============================")
print("Simulation Results")
print("==============================")

print(f"Final speed       : {v_list[-1]:.2f} km/h")
print(f"Final acceleration: {a_list[-1]:.2f} g")
print(f"Distance          : {x_list[-1]:.2f} m")


# =========================================================
# Plot
# =========================================================

fig, axes = plt.subplots(
    3,
    1,
    figsize=(10, 10),
    sharex=True
)


# =========================================================
# Position
# =========================================================

axes[0].plot(
    t_list,
    x_list,
    linewidth=2
)

axes[0].set_ylabel("Position (m)")
axes[0].set_title("Acceleration Simulation - Position")
axes[0].grid(True)


# =========================================================
# Velocity
# =========================================================

axes[1].plot(
    t_list,
    v_list,
    linewidth=2
)

axes[1].set_ylabel("Velocity (km/h)")
axes[1].set_title("Acceleration Simulation - Velocity")
axes[1].grid(True)


# =========================================================
# Acceleration
# =========================================================

axes[2].plot(
    t_list,
    a_list,
    linewidth=2
)

axes[2].set_xlabel("Time (s)")
axes[2].set_ylabel("Acceleration (g)")
axes[2].set_title("Acceleration Simulation - Acceleration")
axes[2].grid(True)


# =========================================================
# Layout
# =========================================================

plt.tight_layout()

plt.savefig(
    plot_path,
    dpi=300,
    bbox_inches="tight"
)

plt.show()

print()
print(f"Plot saved to:")
print(plot_path)