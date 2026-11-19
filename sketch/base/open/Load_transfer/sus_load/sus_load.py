import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")

OUTPUT_DIR = Path(__file__).parent

def wheel_load_stiffness(
    mass,
    g,
    aero,
    ax,
    ay,
    cg_height,
    wheelbase,
    front_ratio,
    track_front,
    track_rear,
    k_heave_front,
    k_heave_rear,
    k_roll_front,
    k_roll_rear,
):
    """
    Steady-state wheel loads using suspension stiffness.

    Parameters
    ----------
    mass : float
    g : float
    aero : float
        Total downforce [N]
    ax : float
    ay : float
    cg_height : float
    wheelbase : float
    front_ratio : float
        Static front weight ratio
    track_front : float
    track_rear : float

    k_heave_front : float
        Front axle heave stiffness [N/m]

    k_heave_rear : float
        Rear axle heave stiffness [N/m]

    k_roll_front : float
        Front axle roll stiffness [Nm/rad]

    k_roll_rear : float
        Rear axle roll stiffness [Nm/rad]

    Returns
    -------
    ndarray
        [FL, FR, RL, RR]
    """

    # -------------------------------------------------------
    # Static load
    # -------------------------------------------------------

    W = mass * g + aero

    F_front_static = W * front_ratio
    F_rear_static = W - F_front_static

    # -------------------------------------------------------
    # Pitch load transfer
    # -------------------------------------------------------

    M_pitch = mass * ax * cg_height

    K_pitch = k_heave_front + k_heave_rear

    pitch_front = M_pitch * k_heave_front / K_pitch
    pitch_rear = M_pitch * k_heave_rear / K_pitch

    dF_front = pitch_front / wheelbase
    dF_rear = pitch_rear / wheelbase

    F_front = F_front_static - dF_front
    F_rear = F_rear_static + dF_rear

    # -------------------------------------------------------
    # Roll load transfer
    # -------------------------------------------------------

    M_roll = mass * ay * cg_height

    K_roll = k_roll_front + k_roll_rear

    roll_front = M_roll * k_roll_front / K_roll
    roll_rear = M_roll * k_roll_rear / K_roll

    dF_front_roll = roll_front / track_front
    dF_rear_roll = roll_rear / track_rear

    # +ay = 左轉
    FL = F_front / 2 - dF_front_roll
    FR = F_front / 2 + dF_front_roll

    RL = F_rear / 2 - dF_rear_roll
    RR = F_rear / 2 + dF_rear_roll

    return np.array([FL, FR, RL, RR])


# plot
# ==============================

if __name__ == "__main__":

    # =====================================
    # Vehicle Parameters
    # =====================================

    mass = param.m
    g = 9.81
    aero = param.F_ref

    cg_height = param.h_cog
    wheelbase = param.L
    front_ratio = param.lr/param.L

    track_front = param.tf
    track_rear = param.tr

    k_heave_front = param.K_heave_f
    k_heave_rear = param.K_heave_r

    k_roll_front = param.K_roll_f
    k_roll_rear = param.K_roll_r

    a = param.target_a
    # =====================================
    # Acceleration Grid
    # =====================================

    ax_list = np.linspace(-a*g, a*g, 81)
    ay_list = np.linspace(-a*g, a*g, 81)

    AX, AY = np.meshgrid(ax_list, ay_list)


    # =====================================
    # Wheel Load Map
    # =====================================

    N_map = np.zeros((*AX.shape, 4))

    for i in range(AX.shape[0]):
        for j in range(AX.shape[1]):

            loads = wheel_load_stiffness(
                mass=mass,
                g=g,
                aero=aero,

                ax=AX[i, j],
                ay=AY[i, j],

                cg_height=cg_height,
                wheelbase=wheelbase,
                front_ratio=front_ratio,

                track_front=track_front,
                track_rear=track_rear,

                k_heave_front=k_heave_front,
                k_heave_rear=k_heave_rear,

                k_roll_front=k_roll_front,
                k_roll_rear=k_roll_rear,
            )

            N_map[i, j] = loads

    # =====================================
    # Extract wheel loads
    # =====================================

    FL = N_map[:, :, 0]
    FR = N_map[:, :, 1]
    RL = N_map[:, :, 2]
    RR = N_map[:, :, 3]

    wheel_loads = [
        ("FL", FL),
        ("FR", FR),
        ("RL", RL),
        ("RR", RR),
    ]


    # =====================================
    # Plot
    # =====================================

    fig, axes = plt.subplots(
        2,
        2,
        figsize=(12, 9)
    )

    for ax_plot, (name, data) in zip(axes.flatten(), wheel_loads):

        c = ax_plot.contourf(
            AX / g,
            AY / g,
            data,
            levels=40
        )

        # 輪胎離地邊界
        ax_plot.contour(
            AX / g,
            AY / g,
            data,
            levels=[0],
            colors="red",
            linewidths=2,
        )

        ax_plot.set_title(f"{name} Wheel Load")

        ax_plot.set_xlabel("Longitudinal Acceleration (g)")
        ax_plot.set_ylabel("Lateral Acceleration (g)")

        ax_plot.grid(True)

        fig.colorbar(
            c,
            ax=ax_plot,
            label="Wheel Load (N)"
        )

    plt.suptitle("Steady-State Wheel Load Envelope")

    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "img.png",
        dpi=300
    )
    plt.show()