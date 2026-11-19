import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")


# =====================================
# Parameters
g = 9.81

m = param.m# 車質量
rf = param.lr/param.L         # Front weight distribution
rr = param.lf/param.L          # Rear weight distribution


h = param.h_cog# 重心高度
L = param.L# 軸距

mu_w = param.mu_w

r_w = param.rw

brake_rate = param.brake_rate#目標比例

r_disc_o = param.r_disc_o# 碟盤外徑
d_gap = param.d_gap# 碟盤受力點與外徑間距

mu_pad = param.mu_pad# 來令片摩擦係數

D_mc_f = param.D_mc_f# MC直徑
D_mc_r = param.D_mc_r#14e-3

D_caliper_f = param.D_caliper_f# 卡前直徑
D_caliper_r = param.D_caliper_r

F_driver = param.F_driver# 車手出力

balance_bar = param.balance_bar# balance_bar

N_caliper_f = param.N_caliper_f# 對幾卡鉗
N_caliper_r = param.N_caliper_r

SF = 1.50# 安全係數


# function
def brake_torque_vs_acceleration(a_array, m, g, h_cog, L, r_w):

    M_f = np.zeros_like(a_array)
    M_r = np.zeros_like(a_array)

    for i, a in enumerate(a_array):

        delta = m * a * h_cog / L

        N_f = m * g / 2 + delta
        N_r = m * g / 2 - delta

        mu_eq = a / g

        F_f = N_f * mu_eq
        F_r = N_r * mu_eq

        M_f[i] = F_f * r_w
        M_r[i] = F_r * r_w

    return M_f, M_r

# 計算
# =====================================
# Maximum deceleration
a_max = mu_w * g

Nf_static = m * g * rr
Nr_static = m * g * rf

delta = m * a_max * h / L

N_f = Nf_static + delta
N_r = Nr_static - delta

# Maximum brake force
F_f_max = mu_w * N_f
F_r_max = mu_w * N_r

M_f_axle = F_f_max * r_w
M_r_axle = F_r_max * r_w

M_fw = M_f_axle / 2
M_rw = M_r_axle / 2

print(f"Front axle load  = {N_f:.1f} N")
print(f"Rear axle load   = {N_r:.1f} N")

print(f"Front axle force = {F_f_max:.1f} N")
print(f"Rear axle force  = {F_r_max:.1f} N")

print(f"Front wheel torque = {M_fw:.1f} Nm")
print(f"Rear wheel torque  = {M_rw:.1f} Nm")


# Brake bias
brake_ratio_f = M_fw / (M_fw + M_rw)
brake_ratio_r = M_rw / (M_fw + M_rw)

print(f"\nBrake Bias = {brake_ratio_f*100:.1f}% / {brake_ratio_r*100:.1f}%")

# Pedal Ratio
r_disc = r_disc_o / 2 - d_gap

F_disc_f = M_fw / r_disc
F_disc_r = M_rw / r_disc

F_caliper_f = F_disc_f / (2 * mu_pad)
F_caliper_r = F_disc_r / (2 * mu_pad)

A_caliper_f = (N_caliper_f / 2) * np.pi * (D_caliper_f / 2) ** 2
A_caliper_r = (N_caliper_r / 2) * np.pi * (D_caliper_r / 2) ** 2

P_f = F_caliper_f / A_caliper_f
P_r = F_caliper_r / A_caliper_r

A_mc_f = np.pi * (D_mc_f / 2) ** 2
A_mc_r = np.pi * (D_mc_r / 2) ** 2

F_mc_f = P_f * A_mc_f
F_mc_r = P_r * A_mc_r

PR = (F_mc_f + F_mc_r) / F_driver * SF

print(f"\nRequired Pedal Ratio = {PR:.2f}")


# Result Table
# =====================================
table = pd.DataFrame(
    {
        "Wheel": ["Front", "Rear"],
        "Area Ratio": [
            A_caliper_f / A_mc_f,
            A_caliper_r / A_mc_r,
        ],
        "Caliper Force (N)": [
            F_caliper_f,
            F_caliper_r,
        ],
        "Line Pressure (Pa)": [
            P_f,
            P_r,
        ],
    }
)

print()
print(table)


# Torque demand
# =====================================
a_array = np.linspace(0.01, a_max, 200)

M_f_list, M_r_list = brake_torque_vs_acceleration(
    a_array,
    m,
    g,
    h,
    L,
    r_w,
)

M_total = M_f_list + M_r_list

M_f_real = M_total * brake_rate
M_r_real = M_total * (1 - brake_rate)


# Plot
# =====================================
plt.figure(figsize=(8,5))

# Ideal
plt.plot(
    a_array,
    M_f_list,
    linewidth=2,
    label="Ideal Front"
)

plt.plot(
    a_array,
    M_r_list,
    linewidth=2,
    label="Ideal Rear"
)

# Real
plt.plot(
    a_array,
    M_f_real,
    "--",
    linewidth=2,
    label=f"Target Front ({balance_bar:.0%})"
)

plt.plot(
    a_array,
    M_r_real,
    "--",
    linewidth=2,
    label=f"Target Rear ({1-balance_bar:.0%})"
)

plt.grid(True)
plt.xlabel("Deceleration (m/s²)")
plt.ylabel("Brake Torque (Nm)")
plt.title(f"Brake Torque Requirement (PR : {PR:.2f})")
plt.legend()

plt.tight_layout()

output = Path(__file__).parent / "Torque_Requirement.png"

plt.savefig(output, dpi=300)

plt.show()