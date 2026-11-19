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

output_path = OUTPUT_DIR / "planetary_gear_number_check.png"


# =========================================================
# Parameters
# =========================================================

# 以下參數請依你的齒輪資料設定
M = param.M_gear       # Module [mm]

Ts = param.Ts       # Sun gear teeth
Tp1 = param.Tp1      # Planet gear teeth

n = param.N_gear         # Number of planetary gears


# =========================================================
# Pitch radius
# =========================================================

Rs = Ts * M
Rp1 = Tp1 * M


# =========================================================
# Angle calculation
# =========================================================

theta = 2 * np.arcsin(
    (Rp1 + 2 * M) / (Rp1 + Rs)
)

theta_lim = 2 * np.pi / n

theta_over = 2 * np.pi / (n + 1)


# =========================================================
# Console output
# =========================================================

print(f"角度: {theta:.2f} rad")
print(f"極限角度: {theta_lim:.2f} rad")
print(f"增加齒輪後角度: {theta_over:.2f} rad")


# =========================================================
# 判斷
# =========================================================

if theta > theta_lim:

    result_main = "幾何干涉，需減少行星齒輪數量"
    result_extra = ""

else:

    result_main = "無干涉"

    if theta > theta_over:

        result_extra = "行星齒輪數量極限狀態"

    else:

        result_extra = "可嘗試更多行星齒輪數量"


print(result_main)

if result_extra:
    print(result_extra)


# =========================================================
# Create report figure
# =========================================================

fig, ax = plt.subplots(
    figsize=(10, 6)
)

ax.axis("off")


# =========================================================
# Title
# =========================================================

ax.text(
    0.5,
    0.92,
    "Planetary Gear Number Check",
    ha="center",
    va="center",
    fontsize=12,
    fontweight="bold"
)


# =========================================================
# Parameters
# =========================================================

parameter_text = (
    f"Module M                 : {M:.2f} mm\n"
    f"Sun Gear Teeth Ts        : {Ts}\n"
    f"Planet Gear Teeth Tp1    : {Tp1}\n"
    f"Planet Gear Number n     : {n}\n"
    f"Sun Pitch Radius Rs      : {Rs:.2f} mm\n"
    f"Planet Pitch Radius Rp1  : {Rp1:.2f} mm"
)

ax.text(
    0.08,
    0.85,
    parameter_text,
    ha="left",
    va="top",
    fontsize=12,
    family="monospace"
)


# =========================================================
# Angle results
# =========================================================

angle_text = (
    f"Calculated Angle       : {theta:.4f} rad\n"
    f"Current Limit          : {theta_lim:.4f} rad\n"
    f"Limit with n+1 Planets : {theta_over:.4f} rad"
)

ax.text(
    0.08,
    0.55,
    angle_text,
    ha="left",
    va="top",
    fontsize=12,
    family="monospace"
)


# =========================================================
# Decision
# =========================================================

if theta > theta_lim:

    decision_text = (
        "GEOMETRIC INTERFERENCE\n"
        "Reduce the number of planetary gears."
    )

elif theta > theta_over:

    decision_text = (
        "PLANETARY GEAR NUMBER LIMIT\n"
        "Current configuration is near the limit."
    )

else:

    decision_text = (
        "NO GEOMETRIC INTERFERENCE\n"
        "More planetary gears may be possible."
    )


ax.text(
    0.5,
    0.35,
    decision_text,
    ha="center",
    va="top",
    fontsize=12,
    fontweight="bold"
)


# =========================================================
# Angle comparison diagram
# =========================================================

# Normalize angles for visual bar
angles = [
    theta,
    theta_lim,
    theta_over
]

labels = [
    "Current",
    f"{n} Planets Limit",
    f"{n+1} Planets Limit"
]


ax_bar = fig.add_axes(
    [0.12, 0.08, 0.76, 0.22]
)

ax_bar.barh(
    labels,
    angles
)

ax_bar.set_xlabel(
    "Angular Requirement [rad]"
)

ax_bar.grid(
    axis="x",
    alpha=0.3
)


# =========================================================
# Save
# =========================================================

fig.savefig(
    output_path,
    dpi=200,
    bbox_inches="tight"
)
plt.close(fig)


print("\nPNG report generated:")
print(output_path)