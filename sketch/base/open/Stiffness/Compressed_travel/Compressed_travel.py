import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")

# Constants
g = 9.81

# Vehicle data
m = param.ms          # kg
ax = param.ax         # Longitudinal acceleration (g)
ay = param.ay         # Lateral acceleration (g)

target_s = param.sus_travel

h = param.h_cog         # CG height (m)
L = param.L         # Wheelbase (m)
t = param.t         # Track width (m)

# Sweep allowable suspension compression
s = np.arange(0.0, 0.051, 0.005)

# 計算
# ================================================
# Load transfer force

Fx = m * ax * g * h / (L)
Fy = m * ay * g * h / (t)

# Required stiffness
K_pitch = Fx / (s)
K_roll = Fy / (s)




idx = np.argmin(np.abs(s - target_s))

K_pitch_target = K_pitch[idx]
K_roll_target = K_roll[idx]

print(f"Pitch stiffness @ 25 mm : {K_pitch_target:.1f} N/m")
print(f"Roll stiffness  @ 25 mm : {K_roll_target:.1f} N/m")


# Plot
plt.figure(figsize=(8, 5))

plt.plot(K_pitch, s, "-r", linewidth=2, label="Pitch")
plt.plot(K_roll, s, "-b", linewidth=2, label="Roll")

# Regulation line
plt.axhline(target_s,
            linestyle="--",
            color="black",
            label="25 mm Limit")

# Mark Pitch point
plt.scatter(K_pitch_target, target_s,
            color="red",
            zorder=5)

plt.annotate(
    f"{K_pitch_target:,.0f} N/m",
    (K_pitch_target, target_s),
    xytext=(10, 12),
    textcoords="offset points",
    color="red"
)

# Mark Roll point
plt.scatter(K_roll_target, target_s,
            color="blue",
            zorder=5)

plt.annotate(
    f"{K_roll_target:,.0f} N/m",
    (K_roll_target, target_s),
    xytext=(10, -18),
    textcoords="offset points",
    color="blue"
)

plt.grid(True)

plt.xlabel("Wheel Rate (N/m)")
plt.ylabel("Suspension Compression (m)")
plt.title("Pitch / Roll Stiffness Requirement")

plt.legend()

plt.tight_layout()


# Save figure
output_path = Path(__file__).parent / "Compressed_travel.png"

plt.savefig(output_path, dpi=300)

print(f"\nFigure saved to:\n{output_path}")

plt.show()

# ===========================================================

# Suspension travel -> Vehicle angle
pitch_deg = np.rad2deg(np.arctan(2 * s / L))
roll_deg = np.rad2deg(np.arctan(2 * s / t))

plt.figure(figsize=(8, 5))

plt.plot(s * 1000, pitch_deg,
         "-r",
         linewidth=2,
         label="Pitch")

plt.plot(s * 1000, roll_deg,
         "-b",
         linewidth=2,
         label="Roll")

# Mark regulation limit
target_pitch = np.rad2deg(np.arctan(2 * target_s / L))
target_roll = np.rad2deg(np.arctan(2 * target_s / t))

plt.scatter(target_s * 1000,
            target_pitch,
            color="red")

plt.scatter(target_s * 1000,
            target_roll,
            color="blue")

plt.annotate(
    f"{target_pitch:.2f}°",
    (target_s * 1000, target_pitch),
    xytext=(10, 10),
    textcoords="offset points",
    color="red"
)

plt.annotate(
    f"{target_roll:.2f}°",
    (target_s * 1000, target_roll),
    xytext=(10, 10),
    textcoords="offset points",
    color="blue"
)

plt.grid(True)

plt.xlabel("Suspension Travel (mm)")
plt.ylabel("Vehicle Angle (deg)")
plt.title("Suspension Travel vs Vehicle Pitch / Roll Angle")

plt.legend()

plt.tight_layout()

output_path = Path(__file__).parent / "Travel_vs_Vehicle_Angle.png"

plt.savefig(output_path, dpi=300)

print(f"Figure saved to:\n{output_path}")

plt.show()