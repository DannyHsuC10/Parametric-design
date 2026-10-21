"""
目標最小化負載轉移

由於通常前軸剛性較高所以利用車體幾何去分擔部分附載轉移降低整體轉移峰值同時讓轉移更快發生
優化主要目標為盡可能降低轉移峰值

"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")
current_dir = Path(__file__).parent
import scipy.signal as signal

# ====================================================
# function
def Half_rollcenter_all_model(sus,d_frame,ay,d_roll):# roll 模型

    F_roll = -(sus.k_roll*d_roll)

    # Roll center
    # 理論幾何力
    
    Mx_rc = -ay*(sus.ms)*(sus.h_rc)

    F_frame_cmd = Mx_rc / sus.track

    a_frame = (
        F_frame_cmd
        - sus.k_frame*d_frame
    ) / (sus.ms/2)

    dF_roll = (sus.k_frame*d_frame)

    M_spring = (F_roll)*sus.track

    M_ext = ay*(sus.ms)*(sus.h_cg)

    Mx = M_spring+M_ext+Mx_rc# 總側傾力矩

    alpha_roll = Mx/sus.Ix

    return F_roll,dF_roll,alpha_roll,a_frame

def extract_first_pulse(data, t):

    data = np.asarray(data)

    rate = np.gradient(data,t)


    # 避免全零訊號
    if np.max(np.abs(rate)) < 1e-9:
        return None,None,0,None


    peaks,_ = signal.find_peaks(
        np.abs(rate)
    )


    if len(peaks)==0:
        return None,None,0,None


    peak_idx = peaks[0]

    # ----------------------------
    # 往前找 zero crossing
    # ----------------------------
    start_idx = 0

    for i in range(peak_idx, 1, -1):

        if rate[i] * rate[i-1] <= 0:
            start_idx = i
            break


    # ----------------------------
    # 往後找 zero crossing
    # ----------------------------
    end_idx = len(rate)-1

    for i in range(peak_idx, len(rate)-1):

        if rate[i] * rate[i+1] <= 0:
            end_idx = i+1
            break


    return (
        t[start_idx:end_idx],
        rate[start_idx:end_idx],
        rate[peak_idx],
        peak_idx
    )

def simulate_rc(sus, ay, dt, t):# 多次sweep 模擬

    # 初始狀態
    d_roll = 0.0
    v_roll = 0.0

    d_frame = 0.0
    v_frame = 0.0

    F_roll_log = []
    dF_roll_log = []


    for _ in t:

        F_roll, dF_roll, alpha_roll, a_frame = \
            Half_rollcenter_all_model(
                sus,
                d_frame,
                ay,
                d_roll
            )


        # Roll integration
        v_roll += alpha_roll * dt
        d_roll += v_roll * dt


        # Frame integration
        v_frame += a_frame * dt
        d_frame += v_frame * dt


        F_roll_log.append(F_roll)
        dF_roll_log.append(dF_roll)


    F_roll_log = np.asarray(F_roll_log)
    dF_roll_log = np.asarray(dF_roll_log)


    # ===============================
    # First pulse
    # ===============================

    t_roll, rate_roll, _, _ = \
        extract_first_pulse(
            F_roll_log,
            t
        )


    t_frame, rate_frame, _, _ = \
        extract_first_pulse(
            dF_roll_log,
            t
        )


    # frame interpolation
    rate_frame_interp = np.interp(
        t_roll,
        t_frame,
        rate_frame
    )


    # Total rate
    rate_total = (
        rate_roll
        +
        rate_frame_interp
    )


    peak_total = np.max(
        np.abs(rate_total)
    )

    return peak_total

# ==========================
# Vehicle
# ==========================
class Suspension:

    def __init__(self):

        # Vehicle
        self.ms = param.ms/2

        # Geometry
        self.h_cg = param.h_cog
        self.h_rc = param.h_rc
        self.track = param.t

        # Roll
        self.Ix = param.Ix
        self.k_roll = param.K_roll

        # Frame
        self.k_frame = self.k_roll * 10

sus = Suspension()
#==============================
# Simulation
#==============================
dt = 0.001
t_end = 2.0
t = np.arange(0, t_end, dt)

# 初始狀態
d_roll = 0.0
v_roll = 0.0

d_frame = 0.0
v_frame = 0.0

# 紀錄
F_roll_log = []
dF_roll_log = []

# 假設固定側向加速度
ay = -20      # m/s^2 (約1G)

for _ in t:

    F_roll, dF_roll, alpha_roll, a_frame = \
        Half_rollcenter_all_model(
            sus,
            d_frame,
            ay,
            d_roll
        )

    #==========================
    # Euler Integration
    #==========================

    # Roll
    v_roll += alpha_roll * dt
    d_roll += v_roll * dt

    # Frame
    v_frame += a_frame * dt
    d_frame += v_frame * dt

    #==========================
    # Log
    #==========================

    F_roll_log.append(F_roll)
    dF_roll_log.append(dF_roll)

#=========================================
# Plot
#=========================================

F_roll_log = np.asarray(F_roll_log)
dF_roll_log = np.asarray(dF_roll_log)

# 懸吊
t_roll, rate_roll, peak_roll, idx_roll = \
    extract_first_pulse(
        F_roll_log,
        t
    )


# 車體
t_frame, rate_frame, peak_frame, idx_frame = \
    extract_first_pulse(
        dF_roll_log,
        t
    )

# Total Force

# 將 frame rate 插值到 roll 的時間軸

rate_frame_interp = np.interp(
    t_roll,
    t_frame,
    rate_frame
)

# total rate
rate_total = rate_roll + rate_frame_interp
# 找完整 t_roll 區間最大值

idx_total = np.argmax(np.abs(rate_total))

peak_total = rate_total[idx_total]
print("peak",peak_total)
t_peak_total = t_roll[idx_total]
# ==========================================
# Plot
# ==========================================
plt.figure(figsize=(10,5))

plt.plot(
    t_roll,
    rate_roll,
    linewidth=2,
    label="Suspension"
)


plt.plot(
    t_frame,
    rate_frame,
    linewidth=2,
    label="Frame"
)


plt.plot(
    t_roll,
    rate_total,
    linewidth=3,
    label="Total Rate"
)

# 標記 total 最大值
plt.scatter(
    t[idx_roll],
    peak_roll,
    s=50,
)

plt.scatter(
    t[idx_frame],
    peak_frame,
    s=50
)

# 只標 Total max
plt.scatter(
    t_peak_total,
    peak_total,
    s=80,
    label="Max Total Rate"
)

plt.xlabel("Time (s)")
plt.ylabel("Force Transfer Rate (N/s)")
plt.title("First Load Transfer Pulse Comparison")

plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig(
    current_dir / "Load_Transfer.png",
    dpi=300,
    bbox_inches="tight"
)
plt.show()

# sweeping 分析
#========================================================

rc_ratio_list = np.linspace(0.01,0.99,50)

total_peak_list = []

for ratio in rc_ratio_list:


    # 修改 RC height
    sus.h_rc = ratio * sus.h_cg


    peak_total = simulate_rc(
        sus,
        ay,
        dt,
        t
    )

    total_peak_list.append(
        peak_total
    )

total_peak_list = np.asarray(total_peak_list)
min_idx = np.argmin(total_peak_list)
min_rc_ratio = rc_ratio_list[min_idx]
min_peak = total_peak_list[min_idx]


print(
    "Minimum RC ratio:",
    min_rc_ratio*100,
    "%"
)

print(
    "Minimum Peak Rate:",
    min_peak,
    "N/s"
)

plt.figure(figsize=(9,5))


plt.plot(
    rc_ratio_list*100,
    total_peak_list,
    linewidth=2,
    marker='o'
)

# minimum point

plt.scatter(
    min_rc_ratio*100,
    min_peak,
    s=120,
    label="Minimum Peak"
)


plt.annotate(
    f"Min\nRC = {min_rc_ratio*100:.1f}%\nRC = {sus.h_cg*min_rc_ratio:.2f} m",
    xy=(min_rc_ratio*100, min_peak),
    xytext=(10, 20),
    textcoords="offset points",
    arrowprops=dict(
        arrowstyle="->"
    ),
    fontsize=10
)

plt.xlabel("Roll Center Height (% CG)")
plt.ylabel("Peak Total Load Transfer Rate (N/s)")
plt.title("RC Height vs Peak Total Load Transfer Rate")
plt.grid(True)
plt.legend()
plt.tight_layout()

plt.savefig(
    current_dir / "min_load_change.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()
