"""
分析項目 : 
1. 第一次回到平衡點
2. Overshoot
3. RMS
4. Peak Acceleration
5. Ride Height Recovery
6. 能量消散最快
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")

from scipy.integrate import solve_ivp

current_dir = Path(__file__).parent

# ===============================
# 系統參數
# ===============================
m = param.ms/4      # kg
k = param.Kr    # N/m


# 自然頻率
omega_n = np.sqrt(k / m)          # rad/s
f_n = omega_n / (2 * np.pi)       # Hz


# 臨界阻尼
c_critical = 2 * np.sqrt(k * m)

print(f"Natural angular frequency (omega_n) = {omega_n:.3f} rad/s")
print(f"Natural frequency (fn) = {f_n:.3f} Hz")
print(f"Critical damping (Cc) = {c_critical:.3f} Ns/m")

# 初始條件
x0 = 0.05      # 初始位移 (m)
v0 = 0.0       # 初始速度 (m/s)

# 模擬時間
t = np.linspace(0, 1, 1000)

# ===============================
# 掃描阻尼比
# ===============================

metrics = []
fig, axs = plt.subplots(3, 1, figsize=(10, 10), sharex=True)

for zeta in np.arange(0.1, 1.0, 0.2):

    c = zeta * c_critical

    # 微分方程
    def spring_damper(t, y):
        x, v = y

        dxdt = v
        dvdt = -(c / m) * v - (k / m) * x

        return [dxdt, dvdt]

    sol = solve_ivp(
        spring_damper,
        [t[0], t[-1]],
        [x0, v0],
        t_eval=t
    )

    # 位移
    x = sol.y[0]

    # 速度
    v = sol.y[1]

    # 加速度
    a = -(c / m) * v - (k / m) * x

    # ==========================================================
    # 1. 第一次回到平衡點 (First Zero Crossing)
    # ==========================================================
    cross_idx = np.where(np.diff(np.sign(x)))[0]

    if len(cross_idx) > 0:
        first_cross = sol.t[cross_idx[0]]
    else:
        first_cross = np.nan


    # ==========================================================
    # 2. Overshoot
    # (第一次穿越後最大的反向位移)
    # ==========================================================
    if len(cross_idx) > 0:
        overshoot = np.max(np.abs(x[cross_idx[0]:]))
    else:
        overshoot = 0


    # ==========================================================
    # 3. RMS
    # ==========================================================
    rms_disp = np.sqrt(np.mean(x**2))
    rms_acc = np.sqrt(np.mean(a**2))


    # ==========================================================
    # 4. Peak Acceleration
    # ==========================================================
    peak_acc = np.max(np.abs(a))


    # ==========================================================
    # 5. Ride Height Recovery (Settling Time)
    # 定義：進入 ±5% 並且不再離開
    # ==========================================================
    tol = 0.05 * abs(x0)

    recovery = np.nan

    for i in range(len(x)):
        if np.all(np.abs(x[i:]) <= tol):
            recovery = sol.t[i]
            break


    # ==========================================================
    # 6. Energy Dissipation
    # ==========================================================

    # 初始總能量
    E0 = 0.5*m*v0**2 + 0.5*k*x0**2

    # 每一時刻剩餘能量
    E = 0.5*m*v**2 + 0.5*k*x**2

    # 已耗散能量
    Ed = E0 - E

    # 能量耗散率
    power = c*v**2

    # 最大耗散率
    peak_power = np.max(power)

    # 到95%能量耗散所需時間
    target = 0.95*E0

    idx = np.where(Ed >= target)[0]

    if len(idx):
        t95 = sol.t[idx[0]]
    else:
        t95 = np.nan


    metrics.append({
        "zeta":zeta,
        "first_cross":first_cross,
        "overshoot":overshoot,
        "rms_disp":rms_disp,
        "rms_acc":rms_acc,
        "peak_acc":peak_acc,
        "ride_recovery":recovery,
        "peak_power":peak_power,
        "t95":t95
    })

    axs[0].plot(sol.t, x, label=f"ζ={zeta:.1f}")
    axs[1].plot(sol.t, v, label=f"ζ={zeta:.1f}")
    axs[2].plot(sol.t, a, label=f"ζ={zeta:.1f}")

# ==========================================
# Convert to arrays
# ==========================================

zeta = np.array([m["zeta"] for m in metrics])

first_cross = np.array([m["first_cross"] for m in metrics])
overshoot = np.array([m["overshoot"] for m in metrics])
rms_disp = np.array([m["rms_disp"] for m in metrics])
rms_acc = np.array([m["rms_acc"] for m in metrics])
peak_acc = np.array([m["peak_acc"] for m in metrics])
ride = np.array([m["ride_recovery"] for m in metrics])
peak_power = np.array([m["peak_power"] for m in metrics])
t95 = np.array([m["t95"] for m in metrics])

# ===============================
# 圖形設定
# ===============================

axs[0].set_ylabel("Displacement (m)")
axs[0].set_title("Displacement")
axs[0].grid(True)

axs[1].set_ylabel("Velocity (m/s)")
axs[1].set_title("Velocity")
axs[1].grid(True)

axs[2].set_ylabel("Acceleration (m/s²)")
axs[2].set_xlabel("Time (s)")
axs[2].set_title("Acceleration")
axs[2].grid(True)

# 共用圖例（只顯示一次）
axs[0].legend(loc="upper right")

plt.tight_layout()
save_path_1 = current_dir / "damping_ratio_response.png"
plt.savefig(
    save_path_1,
    dpi=300,
    bbox_inches="tight"
)
plt.show()

fig,axs=plt.subplots(3,2,figsize=(12,12))

axs[0,0].plot(zeta,first_cross,'o-')
axs[0,0].set_title("First Zero Crossing")

axs[0,1].plot(zeta,overshoot,'o-')
axs[0,1].set_title("Overshoot")

axs[1,0].plot(zeta,rms_acc,'o-')
axs[1,0].set_title("RMS Acceleration")

axs[1,1].plot(zeta,peak_acc,'o-')
axs[1,1].set_title("Peak Acceleration")

axs[2,0].plot(zeta,ride,'o-')
axs[2,0].set_title("Ride Height Recovery")

axs[2,1].plot(zeta,t95,'o-')
axs[2,1].set_title("90% Energy Dissipation Time")

for ax in axs.flat:
    ax.grid(True)
    ax.set_xlabel("Damping Ratio")

plt.tight_layout()
save_path_2 = current_dir / "damping_rate_metrics.png"
plt.savefig(
    save_path_2,
    dpi=300,
    bbox_inches="tight"
)
plt.show()

# 權重計算
# ===========================================
def normalize(x):

    x = np.asarray(x, dtype=float)

    if np.any(np.isnan(x)):
        print("Found NaN:", x)

    xmin = np.nanmin(x)
    xmax = np.nanmax(x)

    if np.isclose(xmax, xmin):
        return np.zeros_like(x)

    return (x-xmin)/(xmax-xmin)

first_n = normalize(first_cross)
over_n  = normalize(overshoot)
rms_n   = normalize(rms_acc)
peak_n  = normalize(peak_acc)
ride_n  = normalize(ride)
t95_n   = normalize(t95)

w = np.ones(6)

score = (
      w[0]*first_n
    + w[1]*over_n
    + w[2]*rms_n
    + w[3]*peak_n
    + w[4]*ride_n
    + w[5]*t95_n
)

best = np.argmin(score)

print("Best damping ratio =",zeta[best])
print("Score =",score[best])

# 最終結果
# =================================

plt.figure(figsize=(10,5))

bottom = np.zeros_like(zeta)

labels = [
    ("First", first_n),
    ("Overshoot", over_n),
    ("RMS", rms_n),
    ("Peak", peak_n),
    ("Ride", ride_n),
    ("Energy", t95_n),
]

for name, value in labels:

    plt.bar(
        zeta.astype(str),
        np.round(value,1),
        bottom=bottom,
        label=name
    )

    bottom += value

plt.ylabel("Normalized Cost")
plt.xlabel("Damping Ratio")
plt.title("Contribution of Each Metric")

plt.legend()

plt.grid(axis='y')

plt.tight_layout()
save_path_3 = current_dir / "damping_metric_score.png"
plt.savefig(
    save_path_3,
    dpi=300,
    bbox_inches="tight"
)

plt.show()

print(f"Figure saved to: {save_path_1}")
print(f"Figure saved to: {save_path_2}")
print(f"Figure saved to: {save_path_3}")
