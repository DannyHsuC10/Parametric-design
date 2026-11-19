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

plot_path = OUTPUT_DIR / "normal_load_vs_acceleration.png"


# =========================================================
# Parameters
# =========================================================

g = 9.81

# 以下參數請依你的車輛設定
m = param.m          # Vehicle mass [kg]
l = param.L           # Wheelbase [m]
l_f = param.lf        # CG to front axle [m]
h_cog = param.h_cog      # CG height [m]
mu_w = param.mu_w         # Tire friction coefficient


# Rear axle distance
l_r = l - l_f


# =========================================================
# Static Load
# =========================================================

N_r_static = m * g * l_f / l
N_f_static = m * g - N_r_static

print(f"Rear static load  : {N_r_static:.2f} N")
print(f"Front static load : {N_f_static:.2f} N")


# =========================================================
# Acceleration range
# =========================================================

a_range = np.linspace(
    0.0,
    mu_w * g,
    100
)


# =========================================================
# Normal Load Calculation
# =========================================================

F_x_total = m * a_range

N_r = (
    F_x_total * h_cog
    + m * g * l_f
) / l

N_f = m * g - N_r


# =========================================================
# Maximum Normal Load
# =========================================================

max_N_r = np.max(N_r)
max_N_f = np.max(N_f)

print(f"Maximum Rear Load  : {max_N_r:.2f} N")
print(f"Maximum Front Load : {max_N_f:.2f} N")


# =========================================================
# Minimum Normal Load
# =========================================================

min_N_r = np.min(N_r)
min_N_f = np.min(N_f)

print(f"Minimum Rear Load  : {min_N_r:.2f} N")
print(f"Minimum Front Load : {min_N_f:.2f} N")


# =========================================================
# Plot
# =========================================================

fig, ax = plt.subplots(
    figsize=(8, 6)
)

ax.plot(
    a_range / g,
    N_f,
    linewidth=2,
    label="Front Load"
)

ax.plot(
    a_range / g,
    N_r,
    linewidth=2,
    label="Rear Load"
)

# Static load reference lines
ax.axhline(
    N_f_static,
    linestyle="--",
    label="Front Static"
)

ax.axhline(
    N_r_static,
    linestyle="--",
    label="Rear Static"
)

ax.set_xlabel(
    "Longitudinal Acceleration [g]"
)

ax.set_ylabel(
    "Normal Load [N]"
)

ax.set_title(
    "Normal Load vs Acceleration"
)

ax.legend()

ax.grid(True)


# =========================================================
# Save figure
# =========================================================

fig.savefig(
    plot_path,
    dpi=200,
    bbox_inches="tight"
)

plt.show()
plt.close(fig)


print(f"\nFigure saved to:")
print(plot_path)