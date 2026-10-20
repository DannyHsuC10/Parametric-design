import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")

from scipy.integrate import solve_ivp

# ==========================================
# Parameters
# ==========================================

# damping coefficient
# underdamped: c < 2*sqrt(m*k)
# critical:    c = 2*sqrt(m*k)
# overdamped:  c > 2*sqrt(m*k)

m = param.ms/4        # mass (kg)
k = param.Kr       # spring stiffness (N/m)
c = param.cr        # damping coefficient (N*s/m)


# ==========================================
# Derived parameters
# ==========================================

wn = np.sqrt(
    k / m
)


zeta = c / (
    2 * np.sqrt(m*k)
)

# ==========================================
# ODE function
# ==========================================

def damped_oscillator(t, y):

    x = y[0]

    v = y[1]


    dxdt = v


    dvdt = (
        -(c/m) * v
        -(k/m) * x
    )


    return [
        dxdt,
        dvdt
    ]

# ==========================================
# Simulation setup
# ==========================================

t_span = (
    0,
    20
)


y0 = [
    1,     # initial displacement
    0      # initial velocity
]

# ==========================================
# Solve ODE45 equivalent
# ==========================================

sol = solve_ivp(
    damped_oscillator,
    t_span,
    y0,
    rtol=1e-6,
    atol=1e-8,
    dense_output=True
)


t = sol.t

x = sol.y[0]

v = sol.y[1]



# ==========================================
# Time response plot
# ==========================================

plt.figure(
    figsize=(8,5)
)


plt.plot(
    t,
    x,
    linewidth=1.5
)


plt.xlabel(
    "t (s)"
)


plt.ylabel(
    "x(t)"
)


plt.title(
    f"Damped Oscillator: "
    f"zeta = {zeta:.3f}, "
    f"wn = {wn:.3f} rad/s"
)


plt.grid(True)


plt.tight_layout()



save_path_1 = (
    Path(__file__).parent /
    "damped_oscillator_response.png"
)


plt.savefig(
    save_path_1,
    dpi=300,
    bbox_inches="tight"
)


plt.show()



# ==========================================
# Phase portrait
# ==========================================

plt.figure(
    figsize=(6,6)
)


plt.plot(
    x,
    v,
    linewidth=1.5
)


plt.xlabel(
    "x"
)


plt.ylabel(
    "dx/dt"
)


plt.title(
    "Phase Portrait"
)


plt.grid(True)


plt.tight_layout()



save_path_2 = (
    Path(__file__).parent /
    "damped_oscillator_phase.png"
)


plt.savefig(
    save_path_2,
    dpi=300,
    bbox_inches="tight"
)


plt.show()



# ==========================================
# Summary
# ==========================================

print(
    f"wn = {wn:.4f} rad/s, "
    f"damping ratio zeta = {zeta:.4f}"
)


if zeta < 1:

    print(
        "Case: Underdamped (oscillatory)"
    )


elif abs(zeta - 1) < 1e-6:

    print(
        "Case: Critically damped"
    )


else:

    print(
        "Case: Overdamped (non-oscillatory)"
    )



print(
    f"Saved:\n{save_path_1}\n{save_path_2}"
)