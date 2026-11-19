import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")

# ==========================================================
# Parameters
# ==========================================================

g = 9.81

m = param.m          # kg
mu = param.mu_w

rho = 1.225        # kg/m^3
A = param.A_air            # m^2

target_a = param.target_a

# 速度 (km/h)
v_kmh = np.arange(20, 101, 10)

# km/h -> m/s
v = v_kmh / 3.6

# ==========================================================
# Required Downforce
# ==========================================================

ay = target_a * g

F_required = m * ay

F_tire_without_aero = mu * m * g

F_down_required = F_required / mu - m * g

print(f"Target lateral acceleration : {target_a:.2f} g")
print(f"Vehicle mass                : {m:.1f} kg")
print(f"Required tire force         : {F_required:.1f} N")
print(f"Required downforce          : {F_down_required:.1f} N")
print()

# ==========================================================
# Required CL
# ==========================================================

CL = (
    2 * F_down_required
    / (rho * A * v**2)
)

print(" Speed(km/h)    Required CL")
print("-----------------------------")

for speed, cl in zip(v_kmh, CL):
    print(f"{speed:8.0f}      {cl:8.3f}")

# plot
# ==================================================



current_dir = Path(__file__).parent

plt.figure(figsize=(8, 6))


plt.plot(
    v_kmh,
    CL,
    marker="o",
    linewidth=2,
    label="Required $C_L$"
)


# ==========================================================
# 標註每個點
# ==========================================================

for speed, cl in zip(v_kmh, CL):

    plt.annotate(
        f"{speed:.0f} km/h\nCL={cl:.2f}",
        xy=(speed, cl),
        xytext=(0, 10),
        textcoords="offset points",
        ha="center",
        fontsize=9
    )


# ==========================================================
# Figure setting
# ==========================================================

plt.xlabel(
    "Vehicle Speed (km/h)"
)

plt.ylabel(
    "Required Lift Coefficient $C_L$"
)

plt.title(
    "Required Lift Coefficient vs Speed"
)

plt.grid(True)

plt.legend()


plt.tight_layout()


plt.savefig(
    current_dir / "required_CL.png",
    dpi=300,
    bbox_inches="tight"
)


plt.show()