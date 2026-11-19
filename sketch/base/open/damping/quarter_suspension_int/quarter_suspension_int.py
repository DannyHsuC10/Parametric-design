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

g = 9.81


# Sprung mass

ms = param.ms / 4


# Unsprung mass

mu = param.mu



# ==========================================
# Suspension parameters
# ==========================================

ks = param.Ks       # spring stiffness

kt = param.Kt       # tire stiffness

c = param.cr         # damping



# Initial velocity

vs = 0.0

vu = 0.0



# ==========================================
# Static equilibrium initialization
# ==========================================

# Unsprung force

Fu_i = -(ms + mu) * g


# Sprung force

Fs_i = -ms * g



# Tire compression

zu = Fu_i / kt


# Sprung displacement

zs = zu + Fs_i / ks



zr = 0.0



# ==========================================
# Simulation setup
# ==========================================

dt = 0.001

t = 0.0


T_end = 5



# Storage

as_list = []

zs_list = []

t_list = []



# ==========================================
# Euler integration
# ==========================================

while t < T_end:


    # Road step input

    if t > 1.0:
        zr = 0.05
    else:
        zr = 0.0



    # Suspension force

    Fs = ks * (zu - zs)


    # Damper force

    Fd = c * (vu - vs)


    # Tire force

    Ft = kt * (zr - zu)



    # Accelerations

    a_s = (
        -ms*g
        + Fs
        + Fd
    ) / ms



    a_u = (
        -mu*g
        - Fs
        - Fd
        + Ft
    ) / mu



    # Update time

    t += dt



    # Velocity update

    vs += a_s * dt

    vu += a_u * dt



    # Position update

    zs += vs * dt

    zu += vu * dt



    # Save data

    as_list.append(
        a_s
    )

    zs_list.append(
        zs
    )

    t_list.append(
        t
    )



# Convert numpy array

t_list = np.array(t_list)

zs_list = np.array(zs_list)

as_list = np.array(as_list)



# ==========================================
# Maximum value
# ==========================================

maxZs = np.max(
    zs_list
)


maxAs = np.max(
    as_list
)



print(
    f"Maximum Position of Spring: {maxZs:.6f} m"
)


print(
    f"Maximum Acceleration: {maxAs:.6f} m/s^2"
)



# ==========================================
# Plot
# ==========================================

fig, ax = plt.subplots(
    2,
    1,
    figsize=(9,7),
    sharex=True
)



# Position

ax[0].plot(
    t_list,
    zs_list,
    linewidth=2
)


ax[0].set_ylabel(
    "Position of Spring (m)"
)


ax[0].set_title(
    "Position of Spring Over Time"
)


ax[0].grid(True)



# Acceleration

ax[1].plot(
    t_list,
    as_list,
    linewidth=2
)


ax[1].set_xlabel(
    "Time (s)"
)


ax[1].set_ylabel(
    "Acceleration (m/s²)"
)


ax[1].set_title(
    "Sprung Acceleration"
)


ax[1].grid(True)



plt.tight_layout()



# ==========================================
# Save figure
# ==========================================

save_path = (
    Path(__file__).parent /
    "quarter_car_euler_response.png"
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