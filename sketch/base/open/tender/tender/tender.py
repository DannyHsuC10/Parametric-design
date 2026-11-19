import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys
import pandas as pd
from scipy.optimize import root

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")

# ==========================================
# 1. 車輛與懸吊參數設定 (依據你的描述設定)
# ==========================================
m_car = param.m            # 車重 (kg)
g = 9.81                  # 重力加速度 (m/s^2)
W_total = m_car * g       # 總車重 (N)

# Heave 剛性設定 (N/mm)
k_main_heave = param.K_heave_main/1000    # Main Heave 剛性
tender_rate = param.tender_rate
k_tender_heave = tender_rate * k_main_heave # Tender Heave 剛性

# 串聯後 Heave 初段總剛性 (N/mm)
k_total_heave = (k_main_heave * k_tender_heave) / (k_main_heave + k_tender_heave) # N/mm

# 車輛幾何參數 (用於 Pitch 計算)
wheelbase = param.L         # 軸距 L (m)
h_cg = param.h_cog              # 重心高度 (m)
front_weight_dist = param.lr/param.L  # 前軸重分配比例
anti_dive = param.anti          # 抗俯仰幾何比
# ==========================================
# 計算 10% 空力下壓力量吃掉的總行程
# ==========================================
downforce_10pct = param.cp_k * W_total # 10% 車重下壓力 (N)

# 此時 Tender 未壓滿，使用串聯總剛性 k_total_heave
heave_stroke_10pct = downforce_10pct / k_total_heave

# Tender 彈簧幾何極限
# 假設 Tender 可被壓縮的最大自由行程 (Bind stroke)
# 若已知實際規格可自行修改此數值 (單位: mm)
tender_max_stroke = heave_stroke_10pct

print("="*60)
print(f"總車重 W: {W_total:.2f} N")
print(f"10% 車重下壓力: {downforce_10pct:.2f} N")
print(f"Heave 串聯初段剛性: {k_total_heave:.3f} N/mm")
print(f"在 10% 下壓力下，吃掉的 Heave 總行程為: {heave_stroke_10pct:.2f} mm")
print("="*60)


# ==========================================
# 不同下壓力與加速度下的 Heave 行程與 Pitch 角
# ==========================================
def series_force(x, k_main, k_tender, tender_max_stroke):
    """
    位移 -> 力
    Tender + Main 串聯

    x:
        total spring displacement (mm)

    return:
        force (N)
        status
    """

    # 第一階段等效剛性
    k_eq = (
        k_main * k_tender /
        (k_main + k_tender)
    )


    # Tender bind 前總位移
    # x = xt + xm
    # xt = F/kt
    # xm = F/km
    #
    # 當 xt=tender_max_stroke

    F_bind = k_tender * tender_max_stroke

    x_main_at_bind = F_bind / k_main

    x_bind = (
        tender_max_stroke +
        x_main_at_bind
    )


    if x <= x_bind:

        # Tender + Main 串聯
        F = k_eq*x

        status = "Tender"


    else:

        # bind 後只剩 Main

        F = (
            F_bind*k_main/k_main
            +
            k_main*(x-x_bind)
        )

        status = "Main"


    return F, status

def suspension_equilibrium(
    downforce,
    ax
):

    deltaW = (
        m_car*ax*g*h_cg/wheelbase
    )

    deltaW *= (1-anti_dive)


    F_total = W_total+downforce


    def error(x):

        xf,xr=x


        Ff,_ = series_force(
            xf,
            k_main_heave,
            k_tender_heave,
            tender_max_stroke
        )

        Fr,_ = series_force(
            xr,
            k_main_heave,
            k_tender_heave,
            tender_max_stroke
        )


        eq1 = Ff+Fr-F_total

        eq2 = (Ff-Fr)-2*deltaW


        return [
            eq1,
            eq2
        ]


    sol=root(
        error,
        [10,10]
    )


    xf,xr=sol.x


    return xf,xr

def calculate_heave_and_pitch(downforce_N, a_x_g):

    # ==========================
    # Weight transfer
    # ==========================

    deltaW = (
        m_car *
        a_x_g *
        g *
        h_cg /
        wheelbase
    )

    deltaW *= (1-anti_dive)


    F_total = downforce_N


    # ==========================
    # Solve suspension position
    # ==========================

    def residual(x):

        xf, xr = x


        F_front, status_f = series_force(
            xf,
            k_main_heave,
            k_tender_heave,
            tender_max_stroke
        )


        F_rear, status_r = series_force(
            xr,
            k_main_heave,
            k_tender_heave,
            tender_max_stroke
        )


        # 總垂直力平衡
        eq_force = (
            F_front +
            F_rear -
            F_total
        )


        # Pitch moment 平衡
        eq_pitch = (
            F_front -
            F_rear -
            2*deltaW
        )


        return [
            eq_force,
            eq_pitch
        ]


    # 初始猜測
    sol = root(
        residual,
        [10,10]
    )


    if not sol.success:
        pass
        #print("Solver failed")


    front_stroke, rear_stroke = sol.x


    # ==========================
    # Output
    # ==========================

    heave = (
        front_stroke+
        rear_stroke
    )/2


    pitch_rad = np.arctan(
        (front_stroke-rear_stroke)/
        (wheelbase*1000)
    )


    pitch_deg = np.degrees(pitch_rad)


    _, front_status = series_force(
        front_stroke,
        k_main_heave,
        k_tender_heave,
        tender_max_stroke
    )


    _, rear_status = series_force(
        rear_stroke,
        k_main_heave,
        k_tender_heave,
        tender_max_stroke
    )


    return (
        heave,
        pitch_deg,
        front_stroke,
        rear_stroke,
        f"Front:{front_status} Rear:{rear_status}"
    )

# 測試矩陣：不同下壓力比例 (0% ~ 20%) 與 煞車加速度 (0.5g ~ 2.0g)
downforce_ratios = [0.0, 0.05, 0.10, 0.15, 0.20] # 0% 到 20% 車重
a_x_list = np.linspace(0,2.0,41)

results = []

for df_ratio in downforce_ratios:
    df_val = df_ratio * W_total
    for ax in a_x_list:
        heave, pitch, front, rear, status = calculate_heave_and_pitch(df_val, ax)

        results.append({

            "downforce": df_ratio*100,
            "ax": ax,

            "heave": heave,
            "front": front,
            "rear": rear,

            "pitch": pitch,

            "status": status

        })




df = pd.DataFrame(results)

fig, axs = plt.subplots(2, 2, figsize=(12, 10))

# ==========================================
# Front Stroke
# ==========================================
ax = axs[0, 0]

for df_ratio in downforce_ratios:

    temp = df[df["downforce"] == df_ratio*100]

    ax.plot(
        temp["ax"],
        temp["front"],
        
        linewidth=2,
        label=f'{df_ratio*100:.0f}%'
    )

ax.set_xlabel("Braking Acceleration (g)")
ax.set_ylabel("Front Stroke (mm)")
ax.set_title("Front Suspension Stroke")
ax.grid(True)
ax.legend(title="Downforce")


# ==========================================
# Rear Stroke
# ==========================================
ax = axs[0, 1]

for df_ratio in downforce_ratios:

    temp = df[df["downforce"] == df_ratio*100]

    ax.plot(
        temp["ax"],
        temp["rear"],
        
        linewidth=2,
        label=f'{df_ratio*100:.0f}%'
    )

ax.set_xlabel("Braking Acceleration (g)")
ax.set_ylabel("Rear Stroke (mm)")
ax.set_title("Rear Suspension Stroke")
ax.grid(True)
ax.legend(title="Downforce")


# ==========================================
# Heave
# ==========================================
ax = axs[1, 0]

for df_ratio in downforce_ratios:

    temp = df[df["downforce"] == df_ratio*100]

    ax.plot(
        temp["ax"],
        temp["heave"],
        
        linewidth=2,
        label=f'{df_ratio*100:.0f}%'
    )

ax.set_xlabel("Braking Acceleration (g)")
ax.set_ylabel("Heave (mm)")
ax.set_title("Vehicle Heave")
ax.grid(True)
ax.legend(title="Downforce")


# ==========================================
# Pitch
# ==========================================
ax = axs[1, 1]

for df_ratio in downforce_ratios:

    temp = df[df["downforce"] == df_ratio*100]

    ax.plot(
        temp["ax"],
        temp["pitch"],
        
        linewidth=2,
        label=f'{df_ratio*100:.0f}%'
    )

ax.set_xlabel("Braking Acceleration (g)")
ax.set_ylabel("Pitch (deg)")
ax.set_title("Vehicle Pitch")
ax.grid(True)
ax.legend(title="Downforce")

plt.tight_layout()

save_path_1 = Path(__file__).parent / "tender_heave_pitch_response.png"
plt.savefig(
    save_path_1,
    dpi=300,
    bbox_inches="tight"
)

plt.show()

# ==========================================
# Pitch Gradient d(theta)/d(ax)
# ==========================================

plt.figure(figsize=(8,6))

for df_ratio in downforce_ratios:

    temp = df[df["downforce"] == df_ratio*100].copy()

    # 計算 pitch gradient
    pitch_gradient = np.gradient(
        temp["pitch"].values,
        temp["ax"].values
    )

    plt.plot(
        temp["ax"],
        pitch_gradient,
        linewidth=2,
        label=f'{df_ratio*100:.0f}% Downforce'
    )


plt.xlabel("Braking Acceleration (g)")
plt.ylabel("Pitch Gradient (deg/g)")
plt.title("Pitch Gradient vs Braking Acceleration")
plt.grid(True)
plt.legend(title="Downforce")

plt.tight_layout()

save_path_2 = Path(__file__).parent / "tender_pitch_gradient.png"
plt.savefig(
    save_path_2,
    dpi=300,
    bbox_inches="tight"
)

plt.show()

print(f"Figure saved to: {save_path_1}")
print(f"Figure saved to: {save_path_2}")
