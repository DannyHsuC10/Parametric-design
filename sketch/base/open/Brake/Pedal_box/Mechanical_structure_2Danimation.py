import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent


# ============================================================
# Rotation function
# ============================================================

def rotate(point, center, theta):

    R = np.array([
        [np.cos(theta), -np.sin(theta)],
        [np.sin(theta),  np.cos(theta)]
    ])

    return center + R @ (point - center)


# Geometry
P0 = np.array([0.0, 0.0])        # Pedal pivot
P1_0 = np.array([0.0, 220.0])    # Foot point
P2_0 = np.array([60.0, 160.0])   # Sensor connection

sensor_base = np.array([80.0, 40.0])


# Animation parameters
theta_min = np.deg2rad(0.0)
theta_max = np.deg2rad(12.0)

theta_step = np.deg2rad(0.25)

fps = 30


# 計算
# ================================================================

# Create angle sequence
theta_forward = np.arange(
    theta_min,
    theta_max + theta_step,
    theta_step
)

theta_backward = np.arange(
    theta_max,
    theta_min - theta_step,
    -theta_step
)

theta_list = np.concatenate([
    theta_forward,
    theta_backward
])


# Figure
# ============================================================

fig, ax = plt.subplots(
    figsize=(9, 6)
)

ax.set_aspect("equal")

ax.set_xlim(-80, 180)
ax.set_ylim(-30, 270)

ax.set_xlabel("X [mm]")
ax.set_ylabel("Y [mm]")

ax.set_title(
    "Triangular Pedal with Linear Sensor"
)

ax.grid(True)


# Static objects
# ============================================================

# Pivot
ax.plot(
    P0[0],
    P0[1],
    "ko",
    markersize=9
)

# Sensor base
ax.plot(
    sensor_base[0],
    sensor_base[1],
    "ko",
    markersize=8
)

# Dynamic objects
# ============================================================

# Pedal
pedal_01, = ax.plot(
    [],
    [],
    linewidth=5,
    color="blue"
)

pedal_12, = ax.plot(
    [],
    [],
    linewidth=5,
    color="blue"
)

pedal_20, = ax.plot(
    [],
    [],
    linewidth=5,
    color="blue"
)


# Foot point
foot_point, = ax.plot(
    [],
    [],
    "o",
    color="red",
    markersize=10
)


# Sensor tip
sensor_tip, = ax.plot(
    [],
    [],
    "o",
    color="green",
    markersize=8
)


# Sensor rod
sensor_rod, = ax.plot(
    [],
    [],
    linewidth=4,
    color="green"
)

# Text information
# ============================================================

info_text = ax.text(
    0.02,
    0.95,
    "",
    transform=ax.transAxes,
    verticalalignment="top",
    fontsize=11,
    bbox=dict(
        facecolor="white",
        alpha=0.8
    )
)

# Animation initialization
# ============================================================

def init():

    pedal_01.set_data([], [])
    pedal_12.set_data([], [])
    pedal_20.set_data([], [])

    foot_point.set_data([], [])

    sensor_tip.set_data([], [])

    sensor_rod.set_data([], [])

    info_text.set_text("")

    return (
        pedal_01,
        pedal_12,
        pedal_20,
        foot_point,
        sensor_tip,
        sensor_rod,
        info_text
    )

# Animation update
# ============================================================

def update(frame):

    theta = theta_list[frame]

    # --------------------------------------------------------
    # Rotate pedal
    # --------------------------------------------------------

    P1 = rotate(
        P1_0,
        P0,
        -theta
    )

    P2 = rotate(
        P2_0,
        P0,
        -theta
    )


    # --------------------------------------------------------
    # Pedal geometry
    # --------------------------------------------------------

    pedal_01.set_data(
        [P0[0], P1[0]],
        [P0[1], P1[1]]
    )

    pedal_12.set_data(
        [P1[0], P2[0]],
        [P1[1], P2[1]]
    )

    pedal_20.set_data(
        [P2[0], P0[0]],
        [P2[1], P0[1]]
    )


    # --------------------------------------------------------
    # Foot point
    # --------------------------------------------------------

    foot_point.set_data(
        [P1[0]],
        [P1[1]]
    )


    # --------------------------------------------------------
    # Sensor
    # --------------------------------------------------------

    sensor_vec = P2 - sensor_base

    sensor_length = np.linalg.norm(
        sensor_vec
    )

    sensor_tip.set_data(
        [P2[0]],
        [P2[1]]
    )

    sensor_rod.set_data(
        [sensor_base[0], P2[0]],
        [sensor_base[1], P2[1]]
    )


    # --------------------------------------------------------
    # Information
    # --------------------------------------------------------

    theta_deg = np.rad2deg(theta)

    info_text.set_text(
        f"Pedal Angle : {theta_deg:6.2f}°\n"
        f"Sensor Length : {sensor_length:7.2f} mm"
    )


    return (
        pedal_01,
        pedal_12,
        pedal_20,
        foot_point,
        sensor_tip,
        sensor_rod,
        info_text
    )


# Create animation
# ============================================================

ani = FuncAnimation(
    fig,
    update,
    frames=len(theta_list),
    init_func=init,
    interval=1000 / fps,
    blit=True,
    repeat=True
)

plt.tight_layout()

plt.show()

# safe
# =============================================================
output_path = OUTPUT_DIR / "pedal_mechanism.gif"

ani.save(
    output_path,
    writer="pillow",
    fps=30,
    dpi=120
)

print(f"Animation saved to:")
print(output_path)