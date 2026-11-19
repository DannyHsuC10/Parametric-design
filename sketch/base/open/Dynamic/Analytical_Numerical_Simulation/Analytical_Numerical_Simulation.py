import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")

OUTPUT_DIR = Path(__file__).parent

# Parameters
# =====================================
m = param.m / 4          # kg
k = param.Kr          # N/m


# 計算
# =====================================
# Natural frequency

wn = np.sqrt(k / m)
fn = wn / (2 * np.pi)

print(f"Natural Frequency = {fn:.2f} Hz")

# Initial conditions
x0 = 0.05            # m
v0 = 0.0             # m/s

# Time settings
dt = 1e-5
t_end = 5

t = np.arange(0, t_end + dt, dt)
N = len(t)


# Analytical solution
x_analytical = (
    x0 * np.cos(wn * t)
    + (v0 / wn) * np.sin(wn * t)
)

# Numerical solution (Explicit Euler)
x_num = np.zeros(N)
v_num = np.zeros(N)
a_num = np.zeros(N)

x_num[0] = x0
v_num[0] = v0

for i in range(N - 1):

    # Acceleration
    a_num[i] = -(k / m) * x_num[i]

    # Velocity update
    v_num[i + 1] = v_num[i] + a_num[i] * dt

    # Position update
    x_num[i + 1] = x_num[i] + v_num[i] * dt

# Last acceleration
a_num[-1] = -(k / m) * x_num[-1]


# Plot comparison
# =====================================
plt.figure(figsize=(8, 5))

plt.plot(
    t,
    x_analytical,
    linewidth=2,
    label="Analytical"
)

plt.plot(
    t,
    x_num,
    "--",
    linewidth=1.5,
    label="Explicit Euler"
)

plt.grid(True)

plt.xlabel("Time (s)")
plt.ylabel("Displacement (m)")
plt.title("Analytical vs Numerical Solution")

plt.legend()

plt.tight_layout()

output_path = OUTPUT_DIR / "Analytical_vs_Explicit_Euler.png"

plt.savefig(
    output_path,
    dpi=300,
    bbox_inches="tight"
)

print(f"Figure saved to:\n{output_path}")

plt.show()

# Error analysis
abs_error = np.abs(x_num - x_analytical)

epsilon = 1e-12

rel_error = abs_error / (np.abs(x_analytical) + epsilon) * 100

# Plot error
fig, ax = plt.subplots(
    2,
    1,
    figsize=(8, 6),
    sharex=True
)

ax[0].plot(
    t,
    abs_error,
    linewidth=2)

ax[0].grid(True)

ax[0].set_ylabel("Absolute Error (m)")
ax[0].set_title("Numerical Error")

ax[1].plot(
    t,
    rel_error,
    linewidth=2)

ax[1].grid(True)

ax[1].set_xlabel("Time (s)")
ax[1].set_ylabel("Relative Error (%)")

plt.tight_layout()

output_path = OUTPUT_DIR / "Explicit_Euler_Error.png"

plt.savefig(
    output_path,
    dpi=300,
    bbox_inches="tight")

print(f"Figure saved to:\n{output_path}")

plt.show()
