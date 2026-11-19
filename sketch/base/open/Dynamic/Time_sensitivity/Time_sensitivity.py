import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")

OUTPUT_DIR = Path(__file__).parent
OUTPUT_DIR.mkdir(exist_ok=True)


# Parameters
# =====================================
m = param.m          # kg
k = param.Kr          # N/m

# Initial conditions
x0 = 0.05            # m
v0 = 0.0             # m/s


# Time settings
t_end = 5.0

dt_list = [1e-2, 1e-3, 1e-4, 1e-5]

# 計算
# =====================================
# Loop over different time steps
for dt in dt_list:

    t = np.arange(0, t_end + dt, dt)
    N = len(t)

    # Initialize
    x = np.zeros(N)
    v = np.zeros(N)
    a = np.zeros(N)

    x[0] = x0
    v[0] = v0

    # Explicit Euler
    for i in range(N - 1):

        # Acceleration
        a[i] = -(k / m) * x[i]

        # Velocity update
        v[i + 1] = v[i] + a[i] * dt

        # Position update
        x[i + 1] = x[i] + v[i] * dt

    # Last acceleration
    a[-1] = -(k / m) * x[-1]


    # Energy calculation
    KE = 0.5 * m * v**2
    PE = 0.5 * k * x**2

    E_total = KE + PE

    E0 = E_total[0]

    # Energy error
    E_error_percent = (E_total - E0) / E0 * 100

    # Plot
    # =====================================

    fig, ax = plt.subplots(
        3,
        1,
        figsize=(8, 8),
        sharex=True
    )

    # -------------------------------------

    ax[0].plot(t, x, linewidth=2)

    ax[0].grid(True)

    ax[0].set_ylabel("Displacement (m)")
    ax[0].set_title(f"Explicit Euler | dt = {dt:g} s")

    # -------------------------------------

    ax[1].plot(t, E_total, linewidth=2)

    ax[1].grid(True)

    ax[1].set_ylabel("Energy (J)")

    # -------------------------------------

    ax[2].plot(t, E_error_percent, linewidth=2)

    ax[2].grid(True)

    ax[2].set_xlabel("Time (s)")
    ax[2].set_ylabel("Energy Error (%)")

    plt.tight_layout()

    # Save figure
    # =====================================

    filename = f"Explicit_Euler_dt_{dt:.0e}.png"

    output_path = OUTPUT_DIR / filename

    plt.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight"
    )

    print(f"Figure saved to:\n{output_path}")

    plt.show()
    