import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.integrate import solve_ivp

# =====================================
# Output directory
# =====================================

OUTPUT_DIR = Path(__file__).parent
OUTPUT_DIR.mkdir(exist_ok=True)

# =====================================
# Parameters
# =====================================

ms = 260 / 4          # Sprung mass (kg)
mu = 15.0             # Unsprung mass (kg)

ks = 22550.0          # Suspension stiffness (N/m)
kt = 100000.0         # Tire stiffness (N/m)

# =====================================
# Initial conditions
# =====================================

xs0 = 0.0
vs0 = 0.0

xu0 = 0.025
vu0 = 0.0

X0 = [xs0, vs0, xu0, vu0]

# =====================================
# Time settings
# =====================================

t0 = 0.0
tf = 5.0
dt = 0.001

t_eval = np.arange(t0, tf + dt, dt)

# =====================================
# ODE
# =====================================

def quarter_car_ode(t, X):

    xs, vs, xu, vu = X

    # Sprung mass acceleration
    a_s = -(ks / ms) * (xs - xu)

    # Unsprung mass acceleration
    a_u = (ks / mu) * (xs - xu) - (kt / mu) * xu

    return [
        vs,
        a_s,
        vu,
        a_u
    ]

# =====================================
# Solve ODE (RK45 ~= MATLAB ode45)
# =====================================

sol = solve_ivp(
    quarter_car_ode,
    (t0, tf),
    X0,
    t_eval=t_eval,
    method="RK45"
)

t = sol.t

xs = sol.y[0]
vs = sol.y[1]

xu = sol.y[2]
vu = sol.y[3]

# =====================================
# Energy
# =====================================

KE = (
    0.5 * ms * vs**2
    + 0.5 * mu * vu**2
)

PE = (
    0.5 * ks * (xs - xu)**2
    + 0.5 * kt * xu**2
)

E = KE + PE

E0 = E[0]

E_error = (E - E0) / E0 * 100

# =====================================
# Plot
# =====================================

fig, ax = plt.subplots(
    3,
    1,
    figsize=(8, 8),
    sharex=True
)

# -------------------------------------

ax[0].plot(
    t,
    xs,
    linewidth=2,
    label="Sprung"
)

ax[0].plot(
    t,
    xu,
    "--",
    linewidth=1.5,
    label="Unsprung"
)

ax[0].grid(True)

ax[0].set_ylabel("Position (m)")

ax[0].legend()

ax[0].set_title("Quarter Car (No Damping) - RK45")

# -------------------------------------

ax[1].plot(
    t,
    E,
    linewidth=2
)

ax[1].grid(True)

ax[1].set_ylabel("Total Energy (J)")

# -------------------------------------

ax[2].plot(
    t,
    E_error,
    linewidth=2
)

ax[2].grid(True)

ax[2].set_xlabel("Time (s)")
ax[2].set_ylabel("Energy Error (%)")

plt.tight_layout()

# =====================================
# Save figure
# =====================================

output_path = OUTPUT_DIR / "Quarter_Car_RK45.png"

plt.savefig(
    output_path,
    dpi=300,
    bbox_inches="tight"
)

print(f"Figure saved to:\n{output_path}")

plt.show()