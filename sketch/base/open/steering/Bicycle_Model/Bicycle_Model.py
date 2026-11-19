import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys
from scipy.integrate import solve_ivp

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")


# ==========================================
# Linear Bicycle Model ODE
# ==========================================

def bicycle_ode(t, x, delta_fun, vx, m, Iz, lf, lr, Cf, Cr):

    vy = x[0]
    r = x[1]

    delta = delta_fun(t)

    # =========================
    # Slip angles
    # =========================

    alpha_f = delta - (vy + lf * r) / vx
    alpha_r = -(vy - lr * r) / vx


    # =========================
    # Tire lateral forces
    # =========================

    Fy_f = Cf * alpha_f
    Fy_r = Cr * alpha_r


    # =========================
    # Vehicle dynamics
    # =========================

    vy_dot = (Fy_f + Fy_r) / m - vx * r

    r_dot = (lf * Fy_f - lr * Fy_r) / Iz


    return [
        vy_dot,
        r_dot
    ]

# ==========================================
# Vehicle parameters
# ==========================================

m = param.m        # kg
Iz = param.Iz         # yaw inertia kg*m^2

lf = param.lf       # front CG distance
lr = param.lr       # rear CG distance

L = lf + lr


Cf = param.Cf        # N/rad
Cr = param.Cr        # N/rad


vx = param.v_ref/3.6          # m/s



# ==========================================
# Simulation setup
# ==========================================

t_start = 0
t_end = 5

t_eval = np.linspace(
    t_start,
    t_end,
    1000
)



# Step steering input

def delta(t):

    if t > 0.5:
        return np.deg2rad(5)

    else:
        return 0.0



# ==========================================
# Initial condition
# ==========================================

x0 = [
    0,      # vy
    0       # yaw rate
]



# ==========================================
# Solve ODE
# ==========================================

sol = solve_ivp(
    bicycle_ode,
    [t_start, t_end],
    x0,
    args=(
        delta,
        vx,
        m,
        Iz,
        lf,
        lr,
        Cf,
        Cr
    ),
    t_eval=t_eval
)


t = sol.t

vy = sol.y[0]

r = sol.y[1]



# ==========================================
# Calculate slip angle
# ==========================================

alpha_f = np.zeros_like(t)

alpha_r = np.zeros_like(t)


for i in range(len(t)):

    d = delta(t[i])

    alpha_f[i] = (
        d -
        (vy[i] + lf*r[i]) / vx
    )

    alpha_r[i] = (
        -(vy[i] - lr*r[i]) / vx
    )



# ==========================================
# Plot
# ==========================================

fig, ax = plt.subplots(
    3,
    1,
    figsize=(8, 8),
    sharex=True
)



# ---- yaw rate ----

ax[0].plot(
    t,
    np.rad2deg(r),
    linewidth=2
)

ax[0].set_ylabel(
    "Yaw Rate (deg/s)"
)

ax[0].grid(True)



# ---- lateral velocity ----

ax[1].plot(
    t,
    vy,
    linewidth=2
)

ax[1].set_ylabel(
    "v_y (m/s)"
)

ax[1].grid(True)



# ---- slip angle ----

ax[2].plot(
    t,
    np.rad2deg(alpha_f),
    linewidth=2,
    label=r"$\alpha_f$"
)


ax[2].plot(
    t,
    np.rad2deg(alpha_r),
    linewidth=2,
    label=r"$\alpha_r$"
)


ax[2].set_ylabel(
    "Slip Angle (deg)"
)

ax[2].set_xlabel(
    "Time (s)"
)

ax[2].legend()

ax[2].grid(True)



fig.suptitle(
    "Linear Bicycle Model Response"
)


plt.tight_layout()



# ==========================================
# Save figure
# ==========================================

save_path = (
    Path(__file__).parent /
    "linear_bicycle_response.png"
)


plt.savefig(
    save_path,
    dpi=300,
    bbox_inches="tight"
)


plt.show()


print(f"Figure saved to: {save_path}")