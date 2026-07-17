from pathlib import Path
from geometry_data import geometry_data
from json_data import file_data
import matplotlib.pyplot as plt
import numpy as np
from wheeltrack import wheel

# ==============================================================================
# 1. 環境與資料初始化
# ==============================================================================
current_dir = Path(__file__).resolve().parent
base_dir = current_dir.parent

figures_dir = current_dir / "Figures"
figures_dir.mkdir(exist_ok=True)

# 載入幾何與輪胎資料
geometry = geometry_data()
geometry.load_json(base_dir / "geometry.json")
data = file_data(base_dir / "tire.json")

# ==============================================================================
# 2. 車輛與模擬參數設定
# ==============================================================================
g = 9.81
front_mass = geometry.m *geometry.CG_rate[0]  # kg
rear_mass = geometry.m * geometry.CG_rate[1]  # kg
cg_height = geometry.h_cog  # m
front_track = geometry.track_front  # m

print(f"Mass - Front: {front_mass:.2f} kg, Rear: {rear_mass:.2f} kg")

# 輪胎模型參數
tir_params = wheel.tir_params
SA_list = [12] * 4
SL_list = [0.0] * 4

# 模擬範圍設定
ay_max = data.mu_y_RL * g  # m/s²
ay_values = np.linspace(g, ay_max, 20)

# 後輪距掃描範圍
num_steps = int((front_track - 1.2) * 100)
rear_track_values = np.linspace(1.2, front_track, num_steps+1)

# 靜態輪荷重計算
static_front_each = front_mass * g / 2  # N
static_rear_each = rear_mass * g / 2  # N


# ==============================================================================
# 3. 核心模擬函式 (避免重複代碼)
# ==============================================================================
def simulate_lat_accel(rear_track):
    """給定後輪距，計算在不同側向加速度下的輪荷重與側向力"""
    out_f, in_f, out_r, in_r = [], [], [], []
    fy_f_list, fy_r_list = [], []

    for ay_i in ay_values:
        # 前/後軸荷重轉移 (Load Transfer)
        dF_front = front_mass * ay_i * cg_height / front_track
        dF_rear = rear_mass * ay_i * cg_height / rear_track

        F_out_front = static_front_each + dF_front / 2
        F_in_front = static_front_each - dF_front / 2
        F_out_rear = static_rear_each + dF_rear / 2
        F_in_rear = static_rear_each - dF_rear / 2

        out_f.append(F_out_front)
        in_f.append(F_in_front)
        out_r.append(F_out_rear)
        in_r.append(F_in_rear)

        # 四輪順序: [FL, FR, RL, RR]
        FZ_list = [F_out_front, F_in_front, F_out_rear, F_in_rear]

        # 呼叫魔術公式 / 輪胎模型
        _, Fy, _, _, _, _ = wheel.Four_wheel_output(
            FZ_list,
            SA_list.copy(),
            SL_list.copy(),
            tir_params,
            IA_list=None,
            P_list=None,
        )

        fy_f_list.append(Fy[0] + Fy[1])
        fy_r_list.append(Fy[2] + Fy[3])

    # 計算側向力變化量
    dFy_front = fy_f_list[0] -fy_f_list

    dFy_rear = fy_r_list[0] - fy_r_list

    delta_LLT = (dFy_front / fy_f_list[0]) - (dFy_rear / fy_r_list[0])

    delta_LLT = np.average(delta_LLT)
    #print(delta_LLT)

    results = {
        "out_f": out_f,
        "in_f": in_f,
        "out_r": out_r,
        "in_r": in_r,
        "fy_f": fy_f_list,
        "fy_r": fy_r_list,
        "delta_LLT": delta_LLT,
    }
    return results


# ==============================================================================
# 4. 執行後輪距掃描 (Rear Track Sweep)
# ==============================================================================
delta_LLT_list = []
delta_LLT_min = np.inf
best_rear_track = front_track

for r_track in rear_track_values:
    res = simulate_lat_accel(r_track)
    delta_LLT_list.append(res["delta_LLT"])

    # 尋找大於 0 且最小的 delta_LLT
    if 0 < res["delta_LLT"] < delta_LLT_min:
        delta_LLT_min = res["delta_LLT"]
        best_rear_track = r_track

# 繪製後輪距掃描圖
plt.figure(figsize=(8, 5))
plt.plot(rear_track_values, delta_LLT_list, "o-", linewidth=2, label="Delta LLT")
plt.xlabel("Rear track (m)")
plt.ylabel("Delta LLT (%)")
plt.title("Rear Track Sweep: Delta LLT vs Rear Track")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig(figures_dir / "rear_track_vs_delta_LLT.png", dpi=300)


# ==============================================================================
# 5. 使用最佳後輪距重新模擬並畫圖
# ==============================================================================
best_res = simulate_lat_accel(best_rear_track)

ay_g = ay_values / g

# 圖一：四輪荷重變化
plt.figure(figsize=(8, 5))
plt.plot(ay_g, best_res["out_f"], "o-", linewidth=2, label="Outside Front (N)")
plt.plot(ay_g, best_res["in_f"], "s-", linewidth=2, label="Inside Front (N)")
plt.plot(ay_g, best_res["out_r"], "o--", linewidth=2, label="Outside Rear (N)")
plt.plot(ay_g, best_res["in_r"], "s--", linewidth=2, label="Inside Rear (N)")
plt.xlabel("Lateral acceleration (g)")
plt.ylabel("Wheel Load (N)")  # 修正原本寫 kg 但實際是 N 的文字錯誤
plt.title(
    f"Wheel Loads vs Lat Accel (Best Rear Track = {best_rear_track:.3f} m)"
)
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig(figures_dir / "wheel_loads_vs_lateral_acceleration.png", dpi=300)

# 圖二：前後軸側向力
plt.figure(figsize=(8, 5))
plt.plot(ay_g, best_res["fy_f"], "s-", linewidth=2, label="Fy_front (N)")
plt.plot(ay_g, best_res["fy_r"], "v-", linewidth=2, label="Fy_rear (N)")
plt.xlabel("Lateral acceleration (g)")
plt.ylabel("Force (N)")
plt.title(
    f"Front/Rear Lateral Forces vs Lat Accel (Best Rear Track = {best_rear_track:.3f} m)"
)
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig(
    figures_dir / "front_rear_wheel_forces_vs_lateral_acceleration.png", dpi=300
)

if geometry.show_plt:
    plt.show()
else:
    plt.close('all')
    

# ==============================================================================
# 6. 輸出最終結果
# ==============================================================================
print(f"\n--- 最佳化結果 (Best Case) ---")
print(f"Best Rear Track: {best_rear_track:.3f} m")
print(f"前後抓地下降比例差異 (delta_LLT): {best_res['delta_LLT']:.4f} N/kg")

geometry.track_rear = best_rear_track

geometry.save_json(base_dir / "geometry.json")

