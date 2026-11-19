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
a = param.target_a          # acceleration (g)
h = param.h_cog         # CG height (m)
L = param.L         # wheelbase (m)
T = param.t      # track width (m)
ay = param.target_a

target_theta = 1
target_phi = 2

# Allowable pitch angle sweep
theta_deg = np.arange(0.1, 3.1, 0.1)
theta = np.deg2rad(theta_deg)

phi_deg = np.arange(0.1, 3.1, 0.1)
phi = np.deg2rad(phi_deg)


# 計算pitch
# =============================================
# Chassis displacement at axle
s = (L / 2) * theta


# Pitch moment
Fx = m * a * g
M = Fx * h
F = M / (L / 2)

# Required stiffness
K = F / (2 * s)


# Find stiffness
idx = np.argmin(np.abs(theta_deg - target_theta))
K_target = K[idx]

print(f"Pitch stiffness @ {target_theta:.1f}° = {K_target:.1f} N/m")

# 計算目標行程
target_s_theta = (L / 2) * np.deg2rad(target_theta)
print(f"Target displacement @ {target_theta:.1f}° = {target_s_theta:.3f} m")


# Roll
# =============================================

# chassis displacement
s_roll = (T/2) * phi

# roll moment
Fy = m * ay * g
M_roll = Fy * h
F_roll = M_roll / (T/2)

# required roll stiffness
K_roll = F_roll / (2 * s_roll)

idx_roll = np.argmin(np.abs(phi_deg - target_phi))
K_roll_target = K_roll[idx_roll]

print(f"Roll stiffness @ {target_phi:.1f}° = {K_roll_target:.1f} N/m")
# 計算目標行程
target_s_phi = (T / 2) * np.deg2rad(target_phi)
print(f"Target displacement @ {target_phi:.1f}° = {target_s_phi:.3f} m")

# Plot
# ============================================
plt.figure(figsize=(8,5))

plt.plot(K, theta_deg, linewidth=2, label="Pitch")
plt.plot(K_roll, phi_deg, linewidth=2, label="Roll")

plt.scatter(K_target, target_theta, color="red")
plt.annotate(
    f"{K_target:,.0f} N/m\n@ {target_theta:.1f}°",
    xy=(K_target, target_theta),
    xytext=(20, 0),
    textcoords="offset points",
    arrowprops=dict(arrowstyle="->")
)

plt.scatter(K_roll_target, target_phi, color="blue")
plt.annotate(
    f"{K_roll_target:,.0f} N/m\n@ {target_phi:.1f}°",
    xy=(K_roll_target, target_phi),
    xytext=(20, 0),
    textcoords="offset points",
    arrowprops=dict(arrowstyle="->")
)


plt.grid(True)
plt.xlabel("Required Stiffness (N/m)")
plt.ylabel("Allowable Angle (deg)")
plt.title("Pitch Stiffness Requirement vs Allowable Pitch Angle")
plt.legend()
plt.tight_layout()


# Save figure
output_path = Path(__file__).parent / "Stiffness_Requirement.png"

plt.savefig(output_path, dpi=300)

print(f"Figure saved to:\n{output_path}")

plt.show()