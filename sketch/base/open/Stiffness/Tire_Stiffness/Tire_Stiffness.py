import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")

OUTPUT_DIR = Path(__file__).parent

# Parameters
MR = param.MR                # Motion ratio
Kt = param.Kt             # Tire stiffness (N/m)

Ks = np.linspace(20000, 80000, 2000)   # Spring stiffness (N/m)

Kr_roll = param.Kr_roll
Kr_heave = param.Kr_heave

Kr_tag = (Kr_roll/2+Kr_heave/2)/2# 等校單輪剛性
"""
分析上需注意!!!

軸剛性>>輪剛性(/2)
單輪同時造成兩個彈簧壓縮因此平均剛性

軸剛性不等於彈簧剛性
F = k(彈簧剛性)*x(單輪抬升量)
單軸2輪力量*2倍壓縮輛等於4倍F
"""
def ride_rate(MR,Kt,Ks):
    # Wheel rate
    Kw = Ks * MR**2

    # Ride rate
    Kr = (Kw * Kt) / (Kw + Kt)
    return Kr

def calc_spring_rate(MR, Kr, Kt):

    Kw = Kr * Kt / (Kt - Kr)
    Ks = Kw / MR**2
    return Ks


# Heave ride
Ks_roll = calc_spring_rate(MR, Kr_roll, Kt*2)


# roll ride
Ks_heave = calc_spring_rate(MR, Kr_heave, Kt*2)


# Ride rate
Kr = ride_rate(MR,Kt,Ks)


# =====================================
# Find target point
# =====================================

# Find spring stiffness corresponding to Kr_tag
idx_tag = np.argmin(np.abs(Kr - Kr_tag))

Ks_tag = Ks[idx_tag]
Kr_tag_actual = Kr[idx_tag]

k_rate = Kr_tag_actual / Ks_tag# 剛性修正

# Plot

# =====================================

plt.figure(figsize=(8, 5))

plt.plot(
    Ks / 1000,
    Kr / 1000,
    linewidth=2,
    label="Ride Rate"
)

# Reference line: without tire stiffness

plt.plot(
    Ks / 1000,
    Ks / 1000,
    linewidth=2,
    label="Spring Rate"
)

# Mark target point
plt.scatter(
    Ks_tag / 1000,
    Kr_tag_actual / 1000,
    color="red",
    s=80,
    zorder=5,
    label="Target"
)

plt.annotate(
    f"Ks = {Ks_tag/1000:.2f} kN/m\n"
    f"Kr = {Kr_tag/1000:.2f} kN/m\n"
    f"Ks_roll = {Ks_roll/1000:.2f} kN/m\n"
    f"Ks_heave = {Ks_heave/1000:.2f} kN/m",
    xy=(Ks_tag / 1000, Kr_tag_actual / 1000),
    xytext=(20, 15),
    textcoords="offset points",
    arrowprops=dict(arrowstyle="->")
)

plt.grid(True)

plt.xlabel("Spring Rate (kN/m)")
plt.ylabel("Ride Rate (kN/m)")
plt.title("Spring Rate vs Ride Rate")

plt.legend()

plt.tight_layout()

# Save figure
# =====================================

output_path = OUTPUT_DIR / "Spring_Rate_vs_Ride_Rate.png"

plt.savefig(output_path, dpi=300)

print(f"Figure saved to:\n{output_path}")

plt.show()