import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")


# ==========================================
# Parameters
# ==========================================

m = param.m/4



# ==========================================
# Spring stiffness range
# ==========================================

k = np.linspace(
    10000,
    300000,
    1000
)



# ==========================================
# Critical damping
# ==========================================

cc = 2 * np.sqrt(
    k * m
)



# ==========================================
# Natural frequency
# ==========================================

fn = (
    1 / (2*np.pi)
) * np.sqrt(
    k / m
)



# ==========================================
# Plot
# ==========================================

fig, ax = plt.subplots(
    2,
    1,
    figsize=(8,8)
)



# ---- Natural frequency ----

ax[0].plot(
    k / 1000,
    fn,
    linewidth=2
)


ax[0].grid(True)


ax[0].set_xlabel(
    "Spring Stiffness (kN/m)"
)


ax[0].set_ylabel(
    "Natural Frequency (Hz)"
)


ax[0].set_title(
    "Natural Frequency vs Spring Stiffness"
)



# ---- Critical damping ----

ax[1].plot(
    k / 1000,
    cc,
    linewidth=2
)


ax[1].grid(True)


ax[1].set_xlabel(
    "Spring Stiffness (kN/m)"
)


ax[1].set_ylabel(
    "Critical Damping (N·s/m)"
)


ax[1].set_title(
    "Critical Damping vs Spring Stiffness"
)



plt.tight_layout()



# ==========================================
# Save figure
# ==========================================

save_path = (
    Path(__file__).parent /
    "critical_damping_analysis.png"
)


plt.savefig(
    save_path,
    dpi=300,
    bbox_inches="tight"
)


plt.show()


print(
    f"Figure saved to: {save_path}"
)