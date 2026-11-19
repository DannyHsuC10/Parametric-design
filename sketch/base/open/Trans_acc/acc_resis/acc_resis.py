import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")

# =========================================================
# Parameters
# =========================================================

g = 9.81

# Vehicle
m = param.m              # Vehicle mass [kg]

# Tire
mu_w = param.mu_w             # Tire friction coefficient
r_w = param.rw            # Wheel radius [m]

# Wheel rotational inertia
I = param.Iw               # Wheel equivalent inertia [kg*m^2]

# Starting drivetrain torque
M_start = param.M_start         # Starting torque [Nm]

# Rolling resistance
Crr = param.Crr

# Vehicle starting resistance
mu_s = param.mu_s

# Slope
theta_slope = 10.0      # [deg]

# Aerodynamics
h = param.h                # Vehicle height [m]
w = param.w                # Vehicle width [m]

C = param.Cd                # Drag coefficient
rho = 1.225            # Air density [kg/m^3]

eta_air = 1.81e-5      # Air dynamic viscosity [Pa*s]

# Vehicle speed
v = param.target_v              # [km/h]

# Drivetrain efficiency
eta = param.eta

# Safety factor
SF = 1.1

# Maximum motor torque
T_motor_max = param.T_motor    # [Nm]


# =========================================================
# Unit conversion
# =========================================================

# km/h -> m/s
v = v / 3.6


# =========================================================
# Wheel resistance
# =========================================================

# ---------------------------------------------------------
# Inertial force
# ---------------------------------------------------------

a_max = mu_w * g

alpha = a_max / r_w

F_inertia = I * alpha / r_w

print(
    f"Maximum inertial force : "
    f"{F_inertia:.2f} N"
)


# ---------------------------------------------------------
# Starting drivetrain resistance
# ---------------------------------------------------------

F_start_w = M_start / r_w

print(
    f"Starting resistance (drivetrain) : "
    f"{F_start_w:.2f} N"
)


# ---------------------------------------------------------
# Rolling resistance
# ---------------------------------------------------------

F_rr = Crr * m * g

print(
    f"Rolling resistance : "
    f"{F_rr:.2f} N"
)


# =========================================================
# Vehicle body resistance
# =========================================================

# ---------------------------------------------------------
# Vehicle starting resistance
# ---------------------------------------------------------

F_start_c = m * g * mu_s

print(
    f"Starting resistance (vehicle) : "
    f"{F_start_c:.2f} N"
)


# ---------------------------------------------------------
# Grade resistance
# ---------------------------------------------------------

F_slope = (
    m
    * g
    * np.sin(np.deg2rad(theta_slope))
)

print(
    f"Grade resistance : "
    f"{F_slope:.2f} N"
)


# ---------------------------------------------------------
# Aerodynamic resistance
# ---------------------------------------------------------

A = h * w

r = np.sqrt(
    h**2 + w**2
)

b = 6 * np.pi * r * eta_air

# Linear aerodynamic resistance
F_air_1 = b * v

# Quadratic aerodynamic resistance
F_air_2 = (
    0.5
    * C
    * rho
    * A
    * v**2
)

F_air = F_air_2 + F_air_1

print(
    f"Maximum aerodynamic resistance : "
    f"{F_air:.2f} N"
)


# =========================================================
# Total resistance estimation
# =========================================================

# ---------------------------------------------------------
# Vehicle body resistance
# ---------------------------------------------------------

resis_car = (
    F_air
    + F_slope
    + F_start_c
)

print(
    f"Vehicle body resistance : "
    f"{resis_car:.2f} N"
)


# ---------------------------------------------------------
# Wheel resistance
# ---------------------------------------------------------

resis_w = (
    F_rr
    + F_start_w
    + F_inertia
)

print(
    f"Wheel resistance : "
    f"{resis_w:.2f} N"
)


# ---------------------------------------------------------
# Total resistance
# ---------------------------------------------------------

resis_all = (
    resis_car / 4
    + resis_w
) / eta

print(
    f"Maximum total resistance : "
    f"{resis_all:.2f} N"
)


# =========================================================
# Starting torque
# =========================================================

torque_start = resis_all * r_w

print(
    f"Maximum starting torque : "
    f"{torque_start:.2f} Nm"
)


# =========================================================
# Gear ratio lower limit
# =========================================================

z = (
    SF
    * torque_start
    / T_motor_max
)

print(
    f"Gear ratio design lower limit : "
    f"{z:.2f}"
)

# =========================================================
# Save Results as PNG
# =========================================================

import matplotlib.pyplot as plt
from pathlib import Path

# Output path
OUTPUT_DIR = Path(__file__).resolve().parent
output_path = OUTPUT_DIR / "vehicle_resistance_result.png"

# =========================================================
# Results
# =========================================================

results = [
    ["Maximum inertial force", f"{F_inertia:.2f} N"],
    ["Starting resistance (drivetrain)", f"{F_start_w:.2f} N"],
    ["Rolling resistance", f"{F_rr:.2f} N"],
    ["Starting resistance (vehicle)", f"{F_start_c:.2f} N"],
    ["Grade resistance", f"{F_slope:.2f} N"],
    ["Maximum aerodynamic resistance", f"{F_air:.2f} N"],
    ["Vehicle body resistance", f"{resis_car:.2f} N"],
    ["Wheel resistance", f"{resis_w:.2f} N"],
    ["Maximum total resistance", f"{resis_all:.2f} N"],
    ["Maximum starting torque", f"{torque_start:.2f} Nm"],
    ["Gear ratio design lower limit", f"{z:.2f}"],
]

# =========================================================
# Create Figure
# =========================================================

fig, ax = plt.subplots(
    figsize=(10, 6)
)

ax.axis("off")

# Title
ax.set_title(
    "Vehicle Resistance Calculation",
    fontsize=18,
    fontweight="bold",
    pad=20
)

# =========================================================
# Table
# =========================================================

table = ax.table(
    cellText=results,
    colLabels=["Parameter", "Result"],
    colWidths=[0.65, 0.25],
    cellLoc="center",
    loc="center",
)

table.auto_set_font_size(False)
table.set_fontsize(12)

# Row height
table.scale(1, 1.8)

# =========================================================
# Save
# =========================================================

plt.savefig(
    output_path,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print(
    f"\nResult image saved to:\n"
    f"{output_path}"
)