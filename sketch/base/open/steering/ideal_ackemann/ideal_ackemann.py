import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")

# ==========================================
# Vehicle parameters
# ==========================================

L = param.L       # Wheelbase (m)
W = param.tf       # Front track width (m)


# ==========================================
# Turning radius range
# ==========================================

R = np.arange(5, 30.5, 0.5)   # 5 ~ 30 m


# ==========================================
# Ackermann steering geometry
# ==========================================

# Inner and outer front wheel steering angle
delta_i = np.arctan(L / (R - W / 2))
delta_o = np.arctan(L / (R + W / 2))


# Convert rad -> degree

delta_i_deg = np.rad2deg(delta_i)
delta_o_deg = np.rad2deg(delta_o)


# Ackermann rate
ackermann_rate = (
    (delta_i_deg - delta_o_deg)
    / delta_i_deg
    * 100
)


# ==========================================
# Plot
# ==========================================

fig, ax = plt.subplots(
    2,
    1,
    figsize=(8, 8),
    sharex=True
)


# ---- Steering angle ----

ax[0].plot(
    R,
    delta_i_deg,
    'r-',
    linewidth=2,
    label="Inner wheel"
)

ax[0].plot(
    R,
    delta_o_deg,
    'b-',
    linewidth=2,
    label="Outer wheel"
)


ax[0].set_ylabel(
    "Steering angle (deg)"
)

ax[0].set_title(
    "Front wheel steering angle under Ackermann geometry"
)

ax[0].legend()
ax[0].grid(True)


# ---- Ackermann rate ----

ax[1].plot(
    R,
    ackermann_rate,
    'b-',
    linewidth=2
)


ax[1].set_xlabel(
    "Turning radius R (m)"
)

ax[1].set_ylabel(
    "Ackermann rate (%)"
)

ax[1].set_title(
    "Ackermann rate vs turning radius"
)

ax[1].grid(True)


plt.tight_layout()


# ==========================================
# Save figure
# ==========================================

save_path = Path(__file__).parent / "ackermann_analysis.png"

plt.savefig(
    save_path,
    dpi=300,
    bbox_inches="tight"
)


plt.show()


print(f"Figure saved to: {save_path}")