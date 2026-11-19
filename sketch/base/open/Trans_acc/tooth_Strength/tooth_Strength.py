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

plot_path = OUTPUT_DIR / "gear_module_vs_teeth.png"


# =========================================================
# Parameters
# =========================================================

tau_ult = 560       # Ultimate strength [MPa]

T_min = 20          # Minimum number of teeth

z = param.z_gear              # Gear ratio

T_motor = param.T_motor        # Motor torque [Nm]

h = 10              # Gear width [mm]

M_min = param.M_gear         # Minimum manufacturable module [mm]

SF = 5              # Safety factor


# =========================================================
# Tooth range
# =========================================================

# MATLAB:
# T_list = T_min:100;

T_list = np.arange(
    T_min,
    101
)


# =========================================================
# Initialize
# =========================================================

M1 = np.zeros_like(
    T_list,
    dtype=float
)

M2 = np.zeros_like(
    T_list,
    dtype=float
)

M_Target = np.zeros_like(
    T_list,
    dtype=float
)

T_node = T_min


# =========================================================
# Calculate required module
# =========================================================

for i, T in enumerate(T_list):

    # -----------------------------------------------------
    # Minimum module based on gear strength
    # -----------------------------------------------------

    M1[i] = np.sqrt(
        (6 * T_motor * z * SF)
        /
        (
            T
            * np.pi
            * h
            * tau_ult
        )
    )


    # -----------------------------------------------------
    # Minimum manufacturing module
    # -----------------------------------------------------

    M2[i] = M_min


    # -----------------------------------------------------
    # Actual selected module
    # -----------------------------------------------------

    M_Target[i] = max(
        M2[i],
        M1[i]
    )


    # -----------------------------------------------------
    # Find transition point
    # -----------------------------------------------------

    if M1[i] > M2[i]:

        M_Target[i] = M1[i]

        print(
            f"第 {T} 齒使用模數 : "
            f"{M_Target[i]:.4f} mm"
        )

        T_node = T


# =========================================================
# Result
# =========================================================

print()
print(
    f"齒數 {T_node} 後都使用最小精度 "
    f"{M_min:.2f} mm"
)


# =========================================================
# Plot
# =========================================================

fig, ax = plt.subplots(
    figsize=(9, 6)
)


# Strength requirement
ax.plot(
    T_list,
    M1,
    linewidth=2,
    label="Strength Requirement"
)


# Manufacturing minimum
ax.plot(
    T_list,
    M2,
    linewidth=2,
    label="Manufacturing Minimum"
)


# Selected module
ax.plot(
    T_list,
    M_Target,
    "--",
    linewidth=2,
    label="Selected Module"
)


# Transition point
ax.axvline(
    T_node,
    linestyle="--",
    linewidth=1.5,
    label=f"Transition: T = {T_node}"
)


# =========================================================
# Plot settings
# =========================================================

ax.set_title(
    "Gear Module vs Sun Gear Tooth Number"
)

ax.set_xlabel(
    "Number of Teeth T"
)

ax.set_ylabel(
    "Module M (mm)"
)

ax.grid(True)

ax.legend()

plt.tight_layout()


# =========================================================
# Save PNG
# =========================================================

plt.savefig(
    plot_path,
    dpi=300,
    bbox_inches="tight"
)

plt.show()

print()
print(f"Plot saved to:")
print(plot_path)