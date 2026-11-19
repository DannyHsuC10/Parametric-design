import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")

OUTPUT_DIR = Path(__file__).parent

from sus_load import wheel_load_stiffness
# =====================================
# Vehicle
# =====================================

g = 9.81
mass = param.m
g = 9.81
aero = param.F_ref

cg_height = param.h_cog
wheelbase = param.L
front_ratio = param.lr/param.L

track_front = param.tf
track_rear = param.tr

k_heave_front = param.K_heave_f
k_heave_rear = param.K_heave_r

k_roll_front = param.K_roll_f
k_roll_rear = param.K_roll_r

a = param.target_a
mu_x = param.mu_x
mu_y = param.mu_y
# =====================================
# Driving condition
# =====================================

ax = a*g
ay = a*g

# =====================================
# Wheel loads
# =====================================

wheel_load = wheel_load_stiffness(
    mass,
    g,
    aero,
    ax,
    ay,
    cg_height,
    wheelbase,
    front_ratio,
    track_front,
    track_rear,
    k_heave_front,
    k_heave_rear,
    k_roll_front,
    k_roll_rear,
)

FL, FR, RL, RR = wheel_load

FL = np.maximum(FL, 0.0)
FR = np.maximum(FR, 0.0)
RL = np.maximum(RL, 0.0)
RR = np.maximum(RR, 0.0)
wheel_load = np.maximum(wheel_load, 0.0)

Fz = wheel_load

# =====================================
# Plot
# =====================================


Fx = mu_x * Fz
Fy = mu_y * Fz

wheel_name = ["FL", "FR", "RL", "RR"]

# =====================================
# Print
# =====================================

print("="*60)

for i in range(4):

    print(
        f"{wheel_name[i]} : "
        f"Fz = {Fz[i]:7.1f} N   "
        f"Fx_max = {Fx[i]:7.1f} N   "
        f"Fy_max = {Fy[i]:7.1f} N"
    )

print("="*60)

# =====================================
# Plot
# =====================================

x = np.arange(4)
width = 0.25

plt.figure(figsize=(10,6))

plt.bar(
    x-width,
    Fz,
    width,
    label="Fz"
)

plt.bar(
    x,
    Fx,
    width,
    label="Fx max"
)

plt.bar(
    x+width,
    Fy,
    width,
    label="Fy max"
)

plt.xticks(x, wheel_name)

plt.ylabel("Force (N)")
plt.title("Maximum Tire Force (μ = 1.7)")
plt.grid(alpha=0.3)
plt.legend()

# 在柱狀圖上標示數值
for i in range(4):

    plt.text(
        x[i]-width,
        Fz[i]+20,
        f"{Fz[i]:.0f}",
        ha="center",
        fontsize=9
    )

    plt.text(
        x[i],
        Fx[i]+20,
        f"{Fx[i]:.0f}",
        ha="center",
        fontsize=9
    )

    plt.text(
        x[i]+width,
        Fy[i]+20,
        f"{Fy[i]:.0f}",
        ha="center",
        fontsize=9
    )

plt.tight_layout()
plt.savefig(
    OUTPUT_DIR / "img2.png",
    dpi=300
)
plt.show()