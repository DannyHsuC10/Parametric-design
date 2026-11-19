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

# 掃描下壓力
F_down = np.linspace(0, 2500, 200)

# ==========================================================
# Lateral acceleration
# ==========================================================

a_y = mu * (m * g + F_down) / m

a_y_g = a_y / g

# ==========================================================
# Plot
# ==========================================================

current_dir = Path(__file__).parent

plt.figure(figsize=(8,5))

plt.plot(
    F_down,
    a_y_g,
    linewidth=2,
    label="Maximum Lateral Acceleration"
)

plt.scatter(
    [0],
    [mu],
    color="red",
    zorder=5,
    label=f"No Aero = {mu:.2f} g"
)

plt.xlabel("Downforce (N)")
plt.ylabel("Lateral Acceleration (g)")
plt.title("Lateral Acceleration vs Downforce")
plt.grid(True)
plt.legend()

plt.tight_layout()

plt.savefig(
    current_dir/"lateral_acceleration_vs_downforce.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()