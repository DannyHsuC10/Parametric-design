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


    # ======================================
    # Road input
    # ======================================

    if t < 0.1:
        xr = 0.0
    else:
        xr = 0.05



    # Suspension relative motion

    dx = xs - xu

    dv = vs - vu



    # Tire deformation

    xt = xu - xr



    # Accelerations

    a_s = (
        -(ks/ms)*dx
        -(cs/ms)*dv
    )


    a_u = (
        (ks/mu)*dx
        +(cs/mu)*dv
        -(kt/mu)*xt
    )



    return [
        vs,
        a_s,
        vu,
        a_u
    ]



# ==========================================
# Parameters
# ==========================================

ms = param.ms / 4       # sprung mass kg

mu = param.mu            # unsprung mass kg


ks = param.Ks         # suspension stiffness N/m

kt = param.Kt        # tire stiffness N/m



# ==========================================
# Damping ratio
# ==========================================

zeta = param.zeta


cc = 2 * np.sqrt(
    ks * ms
)


cs = zeta * cc



print(
    f"Critical damping = {cc:.2f} Ns/m"
)


print(
    f"Suspension damping = {cs:.2f} Ns/m"
)



# ==========================================
# Initial condition
# ==========================================

X0 = [
    0,      # xs
    0,      # vs
    0,      # xu
    0       # vu
]



# ==========================================
# Time
# ==========================================

t_span = (
    0,
    1
)


t_eval = np.linspace(
    0,
    1,
    2000
)



# ==========================================
# Solve ODE
# ==========================================

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
    ),
    rtol=1e-7,
    atol=1e-9
)



t = sol.t

X = sol.y.T



# ==========================================
# Extract states
# ==========================================

xs = X[:,0]

vs = X[:,1]

xu = X[:,2]

vu = X[:,3]



# ==========================================
# Road reconstruction
# ==========================================

xr = np.zeros_like(t)

xr[t >= 0.1] = 0.05



# ==========================================
# Acceleration
# ==========================================

dx = xs - xu

dv = vs - vu


xt = xu - xr



a_s = (
    -(ks/ms)*dx
    -(cs/ms)*dv
)


a_u = (
    (ks/mu)*dx
    +(cs/mu)*dv
    -(kt/mu)*xt
)



# ==========================================
# Energy
# ==========================================

KE = (
    0.5 * ms * vs**2
    +
    0.5 * mu * vu**2
)


PE = (
    0.5 * ks * (xs-xu)**2
    +
    0.5 * kt * xu**2
)


E = KE + PE



# ==========================================
# Plot
# ==========================================

fig, ax = plt.subplots(
    4,
    1,
    figsize=(9,12),
    sharex=True
)



# ---- Position ----

ax[0].plot(
    t,
    xs,
    linewidth=2,
    label="Sprung"
)


ax[0].plot(
    t,
    xu,
    '--',
    linewidth=1.5,
    label="Unsprung"
)


ax[0].set_ylabel(
    "Position (m)"
)

ax[0].grid(True)

ax[0].legend()


ax[0].set_title(
    f"Quarter Car | ζ = {zeta}"
)



# ---- Velocity ----

ax[1].plot(
    t,
    vs,
    linewidth=2,
    label="Sprung"
)


ax[1].plot(
    t,
    vu,
    '--',
    linewidth=1.5,
    label="Unsprung"
)


ax[1].set_ylabel(
    "Velocity (m/s)"
)


ax[1].grid(True)

ax[1].legend()



# ---- Acceleration ----

ax[2].plot(
    t,
    a_s,
    linewidth=2,
    label="Sprung"
)


ax[2].plot(
    t,
    a_u,
    '--',
    linewidth=1.5,
    label="Unsprung"
)


ax[2].set_ylabel(
    "Acceleration (m/s²)"
)


ax[2].grid(True)

ax[2].legend()




# ---- Energy ----

ax[3].plot(
    t,
    E,
    linewidth=2
)


ax[3].set_xlabel(
    "Time (s)"
)


ax[3].set_ylabel(
    "Energy (J)"
)


ax[3].set_title(
    "Energy Dissipation"
)


ax[3].grid(True)



plt.tight_layout()



# ==========================================
# Save figure
# ==========================================

save_path = (
    Path(__file__).parent /
    "quarter_car_energy_response.png"
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