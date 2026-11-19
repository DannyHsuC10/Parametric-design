import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")

# ==========================================================
# Parameters
# ==========================================================

D = 18.25          # Skidpad diameter (m)
g = 9.81

factors = 1.4      # Safety / other factors

mu_tire = param.mu_w
m = param.m

R = D / 2
L = np.pi * D


# ==========================================================
# Sweep lap time
# ==========================================================

t = np.linspace(4.0, 6.0, 200)

# Vehicle speed

v = L / t                 # m/s
v_kmh = v * 3.6           # km/h


# Centripetal acceleration

ac = v**2 / R             # m/s²


# Required equivalent friction coefficient

mu = ac / g * factors


# Required aero contribution ratio

Downforce = (mu / mu_tire-1)*m*g



# ==========================================================
# Marker points
# ==========================================================

mark_times = np.array([
    5.5,
    5.3,
    5.0,
    4.8,
    4.6
])


mark_idx = [
    np.argmin(np.abs(t - tm))
    for tm in mark_times
]


# ==========================================================
# Print reference values
# ==========================================================

idx = np.argmin(np.abs(t - 4.6))

print(f"Time            : {t[idx]:.2f} s")
print(f"Speed           : {v[idx]:.2f} m/s ({v_kmh[idx]:.2f} km/h)")
print(f"Centripetal Acc : {ac[idx]:.2f} m/s²")
print(f"Required μ      : {mu[idx]:.3f}")
print(f"Downforce      : {Downforce[idx]:.3f}")


# ==========================================================
# Plot
# ==========================================================

fig, ax = plt.subplots(
    2,
    2,
    figsize=(12,8)
)


# ==========================================================
# Speed
# ==========================================================

ax[0,0].plot(
    t,
    v_kmh,
    linewidth=2
)

ax[0,0].scatter(
    t[mark_idx],
    v_kmh[mark_idx],
    color="red",
    zorder=5
)


for tm, idx in zip(mark_times, mark_idx):

    ax[0,0].annotate(
        f"{tm:.1f}s\n"
        f"{v_kmh[idx]:.1f} km/h",
        (
            t[idx],
            v_kmh[idx]
        ),
        xytext=(5,8),
        textcoords="offset points",
        fontsize=9
    )

ax[0,0].grid(True)
ax[0,0].set_title("Vehicle Speed")
ax[0,0].set_xlabel("Lap Time (s)")
ax[0,0].set_ylabel("Speed (km/h)")


# ==========================================================
# Lateral acceleration
# ==========================================================

ax[0,1].plot(
    t,
    ac/g,
    linewidth=2
)


ax[0,1].scatter(
    t[mark_idx],
    (ac/g)[mark_idx],
    color="red",
    zorder=5
)


for tm, idx in zip(mark_times, mark_idx):

    ax[0,1].annotate(
        f"{tm:.1f}s\n"
        f"{ac[idx]/g:.2f} g",
        (
            t[idx],
            ac[idx]/g
        ),
        xytext=(5,8),
        textcoords="offset points",
        fontsize=9
    )

ax[0,1].grid(True)
ax[0,1].set_title("Lateral Acceleration")
ax[0,1].set_xlabel("Lap Time (s)")
ax[0,1].set_ylabel("Acceleration (g)")


# ==========================================================
# Required μ
# ==========================================================

ax[1,0].plot(
    t,
    mu,
    linewidth=2
)


ax[1,0].axhline(
    mu_tire,
    color="red",
    linestyle="--",
    label="Tire μ"
)


ax[1,0].scatter(
    t[mark_idx],
    mu[mark_idx],
    color="red",
    zorder=5
)


for tm, idx in zip(mark_times, mark_idx):

    ax[1,0].annotate(
        f"{tm:.1f}s\n"
        f"μ={mu[idx]:.2f}",
        (
            t[idx],
            mu[idx]
        ),
        xytext=(5,8),
        textcoords="offset points",
        fontsize=9
    )


ax[1,0].grid(True)
ax[1,0].legend()
ax[1,0].set_title("Required Friction Coefficient")
ax[1,0].set_xlabel("Lap Time (s)")
ax[1,0].set_ylabel("μ")


# ==========================================================
# Aero ratio
# ==========================================================

ax[1,1].plot(
    t,
    Downforce,
    linewidth=2
)


ax[1,1].axhline(
    1.0,
    color="red",
    linestyle="--"
)


ax[1,1].scatter(
    t[mark_idx],
    Downforce[mark_idx],
    color="red",
    zorder=5
)


for tm, idx in zip(mark_times, mark_idx):

    ax[1,1].annotate(
        f"{tm:.1f}s\n"
        f"{Downforce[idx]:.0f} N",
        (
            t[idx],
            Downforce[idx]
        ),
        xytext=(5,8),
        textcoords="offset points",
        fontsize=9
    )

ax[1,1].grid(True)
ax[1,1].set_title("Required Downforce")
ax[1,1].set_xlabel("Lap Time (s)")
ax[1,1].set_ylabel(
    r"$\mu_{required}/\mu_{tire}$"
)


# ==========================================================
# Save
# ==========================================================

plt.tight_layout()

current_dir = Path(__file__).parent

plt.savefig(
    current_dir / "skidpad_analysis.png",
    dpi=300,
    bbox_inches="tight"
)


plt.show()