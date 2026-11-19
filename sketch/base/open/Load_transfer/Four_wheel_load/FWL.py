import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")

OUTPUT_DIR = Path(__file__).parent


from FWL_solver import four_wheel_load_cg

# ==========================================
# Vehicle parameters (Example)
# ==========================================

g = 9.81

car = SimpleNamespace(
    m=param.m,          # kg
    h=param.h_cog,           # m
    L=param.L,           # wheelbase (m)
    d=param.t,           # track width (m)

    # CG distribution
    CG_x=np.array([param.lr/param.L, param.lf/param.L]),   # Front / Rear
    CG_y=np.array([0.50, 0.50])    # Left / Right
)
a = param.target_a
# ==========================================
# Aerodynamic force
# ==========================================

F_add = np.array([
    0.0,      # Fx
    0.0,      # Fy
    0.0       # Fz
])

CF_rela = np.array([
    0.0,
    0.0,
    0.0
])

# =====================================
# Acceleration sweep
# =====================================

ax_range = np.linspace(
    -a*g,
    a*g,
    50
)

ay_range = np.linspace(
    -a*g,
    a*g,
    50
)


AX, AY = np.meshgrid(
    ax_range,
    ay_range
)


# =====================================
# Allocate
# =====================================

N_map = np.zeros(
    AX.shape + (4,)
)


# =====================================
# Calculate
# =====================================

for idx in np.ndindex(AX.shape):

    ax = AX[idx]
    ay = AY[idx]


    N = four_wheel_load_cg(
        ax=ax,
        ay=ay,
        F_add=F_add,
        CF_rela=CF_rela,
        car=car,
        check=False
    )


    N_map[idx] = N



# =====================================
# Extract wheel load
# =====================================

FL = N_map[:,:,0]
FR = N_map[:,:,1]
RL = N_map[:,:,2]
RR = N_map[:,:,3]


# =====================================
# Plot
# =====================================

wheel_loads = [
    ("FL", FL),
    ("FR", FR),
    ("RL", RL),
    ("RR", RR)
]


fig, axes = plt.subplots(
    2,
    2,
    figsize=(10,8)
)


for ax_plot, (name, data) in zip(
        axes.flatten(),
        wheel_loads):


    c = ax_plot.contourf(
        AX/g,
        AY/g,
        data,
        levels=30
    )


    ax_plot.contour(
        AX/g,
        AY/g,
        data,
        levels=[0],
        colors="red"
    )


    ax_plot.set_title(
        f"{name} Wheel Load"
    )

    ax_plot.set_xlabel(
        "ax (g)"
    )

    ax_plot.set_ylabel(
        "ay (g)"
    )

    fig.colorbar(
        c,
        ax=ax_plot,
        label="Load (N)"
    )


plt.suptitle(
    "Four Wheel Load Envelope"
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "four_wheel_load_surface.png",
    dpi=300
)

plt.show()
# 全分析
# ==============================================

AX, AY = np.meshgrid(ax_range, ay_range)

# =====================================
# Allocate arrays
# =====================================

FL = np.zeros_like(AX)
FR = np.zeros_like(AX)
RL = np.zeros_like(AX)
RR = np.zeros_like(AX)

# =====================================
# Compute wheel loads
# =====================================

for index in np.ndindex(AX.shape):

    ax = AX[index]
    ay = AY[index]
    # CG Method
    N = four_wheel_load_cg(
        ax=ax,
        ay=ay,
        F_add=F_add,
        CF_rela=CF_rela,
        car=car,
        check=False
    )

    FL[index] = N[0]
    FR[index] = N[1]
    RL[index] = N[2]
    RR[index] = N[3]

# =====================================
# Plot
# =====================================

fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection="3d")

colors = [
    "tab:blue",
    "tab:red",
    "tab:green",
    "tab:purple"
]

wheel_names = ["FL", "FR", "RL", "RR"]
wheel_data = [FL, FR, RL, RR]

for color, name, data in zip(colors, wheel_names, wheel_data):

    ax.plot_surface(
        AX,
        AY,
        data,
        color=color,
        alpha=0.5,
        linewidth=0,
        label=name
    )

# 建立 legend（plot_surface 不支援 label）
handles = [
    plt.Rectangle((0, 0), 1, 1, color=c, alpha=0.5)
    for c in colors
]

ax.legend(handles, wheel_names)

ax.set_xlabel("ax (m/s²)")
ax.set_ylabel("ay (m/s²)")
ax.set_zlabel("Wheel Load (N)")

ax.set_title("Four Wheel Loads Overlay vs ax and ay")

ax.view_init(elev=30, azim=45)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "four_wheel_load_overlay.png",
    dpi=300
)

plt.show()
