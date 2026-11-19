import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent

# Parameters
# ==================================================

# Sensor axis position
px = 100.0   # mm
py = 30.0    # mm

sensor_axis = np.array([px, py], dtype=float)
pedal_axis = np.array([0.0, 0.0])


# Pedal geometry
r_pedal = 220.0       # mm
r_sensor = 165.71     # mm

pedal_i_angle_deg = -15.0
sensor_i_angle_deg = -9.5

# Pedal pushing angle
pedal_push_theta_deg = 11.89
pedal_push_theta = np.deg2rad(pedal_push_theta_deg)

# 計算
# ==================================================
# Initial points
pedal_force_point = np.array([
    r_pedal * np.sin(np.deg2rad(pedal_i_angle_deg)),
    r_pedal * np.cos(np.deg2rad(pedal_i_angle_deg))
])

pedal_sensor_point = np.array([
    r_sensor * np.sin(np.deg2rad(sensor_i_angle_deg)),
    r_sensor * np.cos(np.deg2rad(sensor_i_angle_deg))
])


# Rotation function
def rotate_z(point, theta):
    """
    Rotate point around the origin.

    這是為了符合坐標系並沒有用常見的旋轉矩陣定義
    """

    x = point[0]
    y = point[1]

    return np.array([
        x * np.cos(theta) + y * np.sin(theta),
        -x * np.sin(theta) + y * np.cos(theta)
    ])



# Simulation setup
n_step = 101

theta = np.linspace(
    0.0,
    pedal_push_theta,
    n_step
)

theta_deg = np.rad2deg(theta)


pedal_x = np.zeros(n_step)
pedal_y = np.zeros(n_step)

sensor_x = np.zeros(n_step)
sensor_y = np.zeros(n_step)

sensor_length = np.zeros(n_step)


# Main kinematic loop
# ==================================================

for i in range(n_step):

    t = theta[i]

    # Rotate pedal force point
    p_force = rotate_z(
        pedal_force_point,
        t
    )

    # Rotate pedal sensor point
    p_sensor = rotate_z(
        pedal_sensor_point,
        t
    )

    # Pedal force point
    pedal_x[i] = p_force[0]
    pedal_y[i] = p_force[1]

    # Sensor attachment point
    sensor_x[i] = p_sensor[0]
    sensor_y[i] = p_sensor[1]

    # Sensor length
    sensor_length[i] = np.hypot(
        sensor_axis[0] - p_sensor[0],
        sensor_axis[1] - p_sensor[1]
    )


# Derived quantities
# ==================================================

# Sensor length change
delta_sensor_length = -np.diff(sensor_length)

# Pedal X displacement
pedal_x_disp = pedal_x - pedal_x[0]



# Plot 1
# Mechanism movement
# ==================================================

plt.figure(figsize=(8, 6))

plt.plot(
    sensor_x,
    sensor_y,
    linewidth=2,
    label="Sensor Trajectory"
)

plt.plot(
    pedal_x,
    pedal_y,
    linewidth=2,
    label="Pedal Trajectory"
)

# Sensor initial
plt.plot(
    [sensor_x[0], sensor_axis[0]],
    [sensor_y[0], sensor_axis[1]],
    "--",
    label="Sensor Initial"
)

# Sensor final
plt.plot(
    [sensor_x[-1], sensor_axis[0]],
    [sensor_y[-1], sensor_axis[1]],
    "--",
    label="Sensor Final"
)

# Pedal initial
plt.plot(
    [pedal_x[0], pedal_axis[0]],
    [pedal_y[0], pedal_axis[1]],
    "--",
    label="Pedal Initial"
)

# Pedal final
plt.plot(
    [pedal_x[-1], pedal_axis[0]],
    [pedal_y[-1], pedal_axis[1]],
    "--",
    label="Pedal Final"
)

plt.xlabel("X Position [mm]")
plt.ylabel("Y Position [mm]")

plt.title("Mechanism Movement Diagram")

plt.axis("equal")
plt.grid(True)
plt.legend()

plt.tight_layout()

plot_path = OUTPUT_DIR / "mechanism_movement.png"

plt.savefig(
    plot_path,
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# Plot 2
# Pedal Angle vs Sensor Length
# ==================================================

plt.figure(figsize=(8, 5))

plt.plot(
    theta_deg,
    sensor_length,
    linewidth=2
)

plt.xlabel("Pedal Angle [deg]")
plt.ylabel("Sensor Length [mm]")

plt.title("Pedal Angle vs Sensor Length")

plt.grid(True)

plt.tight_layout()

plot_path = OUTPUT_DIR / "pedal_angle_vs_sensor_length.png"

plt.savefig(
    plot_path,
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# Plot 3
# Pedal X vs Sensor Length
# ==================================================

plt.figure(figsize=(8, 5))

plt.plot(
    pedal_x_disp,
    sensor_length,
    linewidth=2
)

plt.xlabel("Pedal X Displacement [mm]")
plt.ylabel("Sensor Length [mm]")

plt.title("Pedal X vs Sensor Length")

plt.grid(True)

plt.tight_layout()

plot_path = OUTPUT_DIR / "pedal_x_vs_sensor_length.png"

plt.savefig(
    plot_path,
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# Plot 4
# Pedal Angle vs Sensor Length Change
# ==================================================

plt.figure(figsize=(8, 5))

plt.plot(
    theta_deg[1:],
    delta_sensor_length,
    linewidth=2
)

plt.xlabel("Pedal Angle [deg]")
plt.ylabel("Sensor Length Change [mm]")

plt.title("Pedal Angle vs Sensor Length Change")

plt.grid(True)

plt.tight_layout()

plot_path = OUTPUT_DIR / "pedal_angle_vs_sensor_length_change.png"

plt.savefig(
    plot_path,
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# Plot 5
# Pedal X vs Sensor Length Change
# ==================================================

plt.figure(figsize=(8, 5))

plt.plot(
    pedal_x_disp[1:],
    delta_sensor_length,
    linewidth=2
)

plt.xlabel("Pedal X Displacement [mm]")
plt.ylabel("Sensor Length Change [mm]")

plt.title("Pedal X vs Sensor Length Change")

plt.grid(True)

plt.tight_layout()

plot_path = OUTPUT_DIR / "pedal_x_vs_sensor_length_change.png"

plt.savefig(
    plot_path,
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# Results
# ==================================================

print("\n==============================")
print("Kinematic Analysis Results")
print("==============================")

print(
    f"Initial Sensor Length = "
    f"{sensor_length[0]:.3f} mm"
)

print(
    f"Final Sensor Length = "
    f"{sensor_length[-1]:.3f} mm"
)

print(
    f"Total Sensor Length Change = "
    f"{delta_sensor_length.sum():.3f} mm"
)

print(
    f"Maximum Sensor Length Change = "
    f"{np.max(delta_sensor_length):.3f} mm"
)

print(
    f"Pedal X Displacement = "
    f"{pedal_x_disp[-1]:.3f} mm"
)

print("\nFigures saved to:")
print(OUTPUT_DIR)