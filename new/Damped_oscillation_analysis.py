import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")

from scipy.integrate import solve_ivp



# ==========================================
# Quarter car ODE
# ==========================================

def quarter_car_damped_ode(
    t,
    X,
    ms,
    mu,
    ks,
    kt,
    cs
):

    # States

    xs = X[0]
    vs = X[1]

    xu = X[2]
    vu = X[3]


    # Relative motion

    dx = xs - xu

    dv = vs - vu



    # Accelerations

    as_ = (
        -(ks/ms)*dx
        -(cs/ms)*dv
    )


    au = (
        (ks/mu)*dx
        +(cs/mu)*dv
        -(kt/mu)*xu
    )



    # State derivatives

    return [
        vs,
        as_,
        vu,
        au
    ]



# ==========================================
# Parameters
# ==========================================

ms = param.ms / 4      # sprung mass (kg)

mu = param.mu           # unsprung mass (kg)


ks = param.Ks        # suspension stiffness (N/m)

kt = param.Kt       # tire stiffness (N/m)


g = 9.81



# ==========================================
# Damping ratios
# ==========================================

zeta_list = [
    0,
    0.2,
    0.4,
    0.7,
    1.0
]



# Critical damping

cc = 2 * np.sqrt(
    ks * ms
)



# ==========================================
# Initial conditions
# ==========================================

xs0 = 0.05

vs0 = 0

xu0 = 0

vu0 = 0


X0 = [
    xs0,
    vs0,
    xu0,
    vu0
]



# ==========================================
# Time
# ==========================================

t_span = (
    0,
    3
)


t_eval = np.linspace(
    0,
    3,
    1000
)



# ==========================================
# Static tire load
# ==========================================

Fz_static = (
    ms + mu
) * g



# ==========================================
# Plot setup
# ==========================================

fig, ax = plt.subplots(
    2,
    1,
    figsize=(9,8),
    sharex=True
)



# ==========================================
# Damping sweep
# ==========================================

for zeta in zeta_list:


    # damping coefficient

    cs = zeta * cc



    # Solve ODE

    sol = solve_ivp(
        quarter_car_damped_ode,
        t_span,
        X0,
        t_eval=t_eval,
        args=(
            ms,
            mu,
            ks,
            kt,
            cs
        )
    )


    t = sol.t

    X = sol.y.T



    # Extract states

    xs = X[:,0]

    xu = X[:,2]



    # Road profile

    xr = np.zeros_like(t)



    # Tire normal load

    Fz = (
        Fz_static
        +
        kt * (xu - xr)
    )



    # Dynamic load variation

    dFz = (
        Fz
        -
        Fz_static
    )



    # Plot sprung displacement

    ax[0].plot(
        t,
        xs,
        linewidth=2,
        label=fr"$\zeta={zeta}$"
    )



    # Plot tire load

    ax[1].plot(
        t,
        dFz,
        linewidth=2,
        label=fr"$\zeta={zeta}$"
    )



# ==========================================
# Formatting
# ==========================================

ax[0].set_ylabel(
    "Sprung Displacement (m)"
)

ax[0].set_title(
    "Damping Ratio Sweep"
)

ax[0].grid(True)

ax[0].legend()



ax[1].set_xlabel(
    "Time (s)"
)

ax[1].set_ylabel(
    "ΔFz (N)"
)

ax[1].set_title(
    "Dynamic Tire Load Variation"
)

ax[1].grid(True)

ax[1].legend()



plt.tight_layout()



# ==========================================
# Save figure
# ==========================================

save_path = (
    Path(__file__).parent /
    "quarter_car_damping_sweep.png"
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