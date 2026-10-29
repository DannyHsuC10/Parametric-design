"""車輛初步設計估算：懸吊、空力、轉向幾何、輪載、傳動與煞車。

在專案主資料夾執行：python "Initial settings/vehicle_initial_sizing.py"。

沿用 analysis/Aero_Stiffness.py 的小角度模型與等效線性剛性定義：
    s = (span / 2) * radians(angle)
    M = ms * acceleration_g * g * h_cog
    K = (M / (span / 2)) / (2 * s)
Pitch 使用軸距 L；Roll 使用輪距 t。K 並非單支彈簧的簧率。
Compressed travel 沿用 analysis/Compressed_travel.py 的公式：
    K = (ms * acceleration_g * g * h_cog / span) / travel
    angle = degrees(atan(2 * travel / span))
目標角度與行程直接代入公式，不取最近的取樣點。
Frequency vs stiffness 沿用 analysis/Frequency_Stiffness.py 的設定：
    K_selected = max(K_angle, K_travel)  # Pitch、Roll 各自比較
    f_n = sqrt(K_selected / (ms / 2)) / (2 * pi)
使用 ms / 2 作為等效計算質量，頻率單位為 Hz。
Tire stiffness 沿用 analysis/Tire_Stiffness.py 的設定：
    Kw = Ks * MR**2
    Kr = Kw * Kt / (Kw + Kt)
一般 Ks 以 (K_roll + K_pitch) / 4 為目標 ride rate，在 20,000～80,000 N/m
的 2,000 個取樣點中選擇最接近者。Pitch、Roll 各自以 2 * Kt 反算簧率。
Frequency vs mass 沿用 analysis/Frequency_mass.py 的未阻尼模態估算：
    Ks_eq = (Ks_roll + Ks_pitch) / 4
    Kw = Ks_eq * MR**2
    Kr = Kw * Kt / (Kw + Kt)
    f_sprung = sqrt(Kr / (ms / 4)) / (2 * pi)
    f_unsprung = sqrt((Kt + Kw) / mu) / (2 * pi)
此項分析的 ms 為全車簧上質量，mu 為單輪簧下質量，均使用 kg。
use_tender = False 時跳過 Heave 反算與 Tender 設計，後續直接採用原 Heave 主簧剛性。
use_tender = True 時，Heave 剛性反算固定 Ks_roll，將 Ks_pitch 視為 heave 剛性：
與 analysis/Frequency_mass.py 相同，以調整前的簧下頻率除以 N 作為目標：
    f_target = f_unsprung_current / N
    Kr_target = (2 * pi * f_target)**2 * (ms / 4)
    Ks_heave_target = 4 * Kr_target * Kt / (Kt - Kr_target) / MR**2 - Ks_roll
再用新 heave 剛性重算簧上與簧下自然頻率。
若固定質量、輪胎及 Roll 剛性下沒有可行的正 heave 剛性，明確回報無解。
2_spring 沿用 analysis/2_spring.py，以原 Pitch/heave 剛性為主簧，
串聯 tender，使等效剛性等於 Frequency vs mass 反算的目標 heave 剛性：
    K_series_target = K_main * Ks_scale_target_frequency
    K_tender = K_series_target * K_main / (K_main - K_series_target)
串聯計算適用於 tender 尚未併圈時。
臨界阻尼使用每軸一支 Heave、一支 Roll 阻尼器，彈簧與阻尼器共用 MR：
    m_front = ms * wf, m_rear = ms * wr
    K_heave_body = K_heave_spring * MR**2
    c_heave_body_crit = 2 * sqrt(K_heave_body * m_axle)
    c_heave_damper_crit = c_heave_body_crit / MR**2
Heave + Tender 使用串聯剛性；純 Heave 使用原主簧剛性（Tender 併圈後）。
Roll 沿用 sus_load 的 K_phi = K_roll_spring * (MR * track)**2：
    C_phi_crit = 2 * sqrt((K_phi_front + K_phi_rear) * Ixx_sprung)
    C_phi_axle = C_phi_crit * K_phi_axle / (K_phi_front + K_phi_rear)
    c_roll_damper_axle = C_phi_axle / (MR * track)**2
這是固定輪端、剛性車體的單自由度參考值；Roll 前後值為同一整車模態的阻尼分配。
四種指定 Ks 另分前後軸逐一代入 Ks → Kw → Kr：
    Ks = (K_heave_with_tender + K_roll) / 2, K_heave_with_tender, K_roll, K_heave_main
    m_wheel = ms * axle_weight_fraction / 2, m_spring_coordinate = m_wheel / MR**2
    Kw = Ks * MR**2, Kr = Kw * Kt / (Kw + Kt)
    f = sqrt(K / m_coordinate) / (2 * pi), c_crit = 2 * sqrt(K * m_coordinate)
Ks 座標用 m_spring_coordinate，Kw／Kr 用 m_wheel；因此 f_Ks = f_Kw。
Kr 臨界阻尼為 ride 等效 SDOF 參考，不直接代表實體阻尼器係數。
Gradient 使用整車慣性力及最終前後彈簧，單位為 deg/g：
    h_roll_axis_at_CG = wf * RC_front + wr * RC_rear
    roll_gradient = degrees(M * g * (h_cog - h_roll_axis_at_CG) / K_phi_total)
Roll 另依 HL 模型串聯各軸輪胎角剛性 Kt * track**2 / 2。
前後相同 Heave 彈簧的 Pitch 角剛性為 K_spring * MR**2 * L**2 / 2。
Pitch 分別輸出串聯／純主簧、僅懸吊／含輪胎與 Anti dive；不取樣求斜率。
Anti dive 使用與前 Roll Center 相同的正規化兩路模型，a 為 anti-dive 分流比例：
    c = K_chassis / K_suspension = rc_chassis_stiffness_ratio
    alpha = c / (1 + c)  # 懸吊路徑比例，依「roll_center_stiffness_derivation.md」的解析解
    K_eq / K_suspension = (1 - a)**2 + c * a**2
    anti_dive = 1 - alpha = 1 / (1 + c), normalized_min_stiffness = c / (1 + c)
此為指定的類比模型設定值；幾何硬點與煞車力分配未在此模型中求解。
依指定定義，以 ax = 2 g、a_acc = 1.2 g 計算 Anti-Scrub：
    anti_scrub = anti_dive * a_acc / ax
roll_center 沿用正規化等效剛性模型，r = h_rc / h_cog，c = Kc / Ks：
    K_eq / Ks = (1 - r)**2 + c * r**2
    r_min = 1 / (1 + c), K_eq_min / Ks = c / (1 + c)
    h_rc = r_min * h_cog
前 RC 與 Anti dive 直接套用「roll_center_stiffness_derivation.md」的解析解。
以前述解析解作為前輪 Roll Center 高度，再依指定比例計算後輪高度：
    h_rc_rear = h_rc_front * (wf / wr) * (tr / tf) * (kf / kr)
FVSA 依指定過程固定以公尺數值計算，d = sus_travel、t 為各軸輪距：
    theta = atan(2 * d / t)  # rad
    FVSA = 1 / tan(theta / (2 * d))
    camber_change = atan(1 / FVSA)  # 按 1 m 位移解讀
    camber_gain_deg_per_m = degrees(camber_change)
    max_camber_change_deg = camber_gain_deg_per_m * d
純 ay 輪胎壓縮：各軸質量依 wf、wr 分配，無縱向加速度、無空力：
    Fy_axle = m_axle * ay * g
    Fz_left + Fz_right = m_axle * g
    (Fz_right - Fz_left) * track / 2 = Fy_axle * h_cog
    compression_left = Fz_left / Kt, compression_right = Fz_right / Kt
    tire_roll_rad = (compression_right - compression_left) / track  # 小角度
保留負輪載的線性外推值；離地時不回傳有效接地模型的輪胎 Roll 角。
Caster 反解使用前軸最大 Roll + 輪胎 Roll - FVSA 最大 Camber 變化，初始 Camber 為 0：
    gamma_base = roll + tire_roll - fvsa_camber_change
    delta_gamma_steer = delta * sin(caster) - (1 - cos(delta)) * sin(kpi)
    applied_camber_change = -delta_gamma_steer  # 固定輪側座標定義
    sin(caster) = (gamma_base + (1 - cos(delta)) * sin(kpi)) / delta
轉向角由指定最小半徑 min_turn_radius_m = 3 m 求解：
    R = L / tan(theta), theta_max = atan(L / R_min)
    delta = degrees(theta_max)  # 單軌等效前輪轉角，沿用已確認的正方向
以 caster = 10 deg 比較 ±delta 只印出方向驗證，不修改求解用的正轉角。
公式內所有角度均用 rad，KPI = 8 deg；求解中不選邊、不依結果正負變號。
原式值另外保留；接地失效時只印線性外推參考。
wf、wr 為前後重量比例，tf、tr 為前後輪距，kf、kr 為前後剛性比例。
重量比例由重心到前軸距離 lf、到後軸距離 lr 的靜態力矩平衡計算：
    L = lf + lr
    wf = lr / L, wr = lf / L
skidpad_test 沿用 analysis/skidpad_test.py，直徑 D = 18.25 m、係數 = 1.4：
    v = pi * D / target_lap_time_s
    ay_skidpad = v**2 / (D / 2)
    mu_required = 1.4 * ay_skidpad / g
    F_down = (mu_required / wl_mu_y - 1) * (ms + 4 * mu) * g
保留原公式的有號下壓力；實際額外所需下壓力最低為 0 N。
空力有效面積 A_air = 1 m^2，空氣密度沿用 Aero_Cl_Cd 的 1.225 kg/m^3：
    C_target = F_down / (rho * A_air * v**2)  # 依指定 F = C * rho * A * v**2
    Cl_standard = 2 * C_target  # 對應原 Aero_Cl_Cd 的 F = 0.5 * Cl * rho * A * v**2
速度取 Skidpad 目標車速（m/s），使用完整所需下壓力；此處係數以下壓力為正。
Tender 壓縮量沿用 analysis/tender.py 的無煞車工況，前後各一組相同彈簧：
    F_assembly = F_down * F_ref_ratio / 2
    s_main = F_assembly / K_main, s_tender = F_assembly / K_tender
    s_total = s_main + s_tender
行程以原平衡位置為零點，只計下壓力造成的增量，輸出換算為 mm。
原 Tender 分析將此下壓力工況設為 tender 壓實的設計切換點。
CG 沿用 analysis/CG.py，以前後較小輪距檢查 45、60 度傾斜幾何上限：
    h_max = min(tf, tr) / (2 * tan(angle) * cg_safety_factor)
    margin = h_max - h_cog
正餘裕為通過；零餘裕為臨界；負餘裕為超過上限。
此項為左右對稱、無懸吊變形的幾何檢查。
sus_load 輪載沿用 analysis/wheel_load/models.py 的懸吊剛性分配：
    m = ms + 4 * mu, D = F_down * F_ref_ratio
    N_front = m * g * wf + D * wl_aero_front_ratio - m * ax * g * h_cog / L
    N_rear = m * g * wr + D * (1 - wl_aero_front_ratio) + m * ax * g * h_cog / L
    K_roll_front = Ks_roll * (MR * tf)**2
    K_roll_rear = Ks_roll * (kr / kf) * (MR * tr)**2
    beta_front = K_roll_front / (K_roll_front + K_roll_rear)
    delta_front = beta_front * m * ay * g * h_cog / tf
    delta_rear = (1 - beta_front) * m * ay * g * h_cog / tr
各軸左右輪載為 N_axle / 2 減／加 delta；正 ax 後軸增載，正 ay 右輪增載。
Fx、Fy 依各輪非負輪載占比分配整車 m * ax * g、m * ay * g，
合力為 sqrt(Fx**2 + Fy**2 + Fz**2)，比較同一工況的四輪。
若原始輪載為負，保留原值並將截零後的三向力標為參考，未重解離地工況。
Gear_rate 使用無空力直線加速工況，ax = a_acc、ay = 0、下壓力 = 0：
    a = a_acc * g, m = ms + 4 * mu
    N_front = m * g * wf - m * a * h_cog / L
    N_rear = m * g * wr + m * a * h_cog / L
    F_front = m * a * N_front / (m * g)
    F_rear = m * a * N_rear / (m * g)
    T_wheel = max(F_front, F_rear) * R_tire / 2
    i_acc = T_wheel / drive_motor_torque_Nm
    n_wheel = (drive_target_speed_kmh / 3.6) / (2 * pi * R_tire) * 60
    i_speed = drive_motor_rpm / n_wheel
    i_avg = (i_acc + i_speed) / 2
沿用 Gear_rate 的輪端扭矩與齒比公式；前後軸配重依本腳本的 wf、wr 定義。
每軸需求力由兩輪均分，每輪對應一顆馬達，未計傳動效率及行駛阻力。
Brake_ratio 使用無空力直線煞車，brake_ax 為正的減速度 g 倍數（車身 ax = -brake_ax）：
    N_front = m * g * wf + m * brake_ax * g * h_cog / L
    N_rear = m * g * wr - m * brake_ax * g * h_cog / L
    B_front = brake_ax * N_front, B_rear = brake_ax * N_rear
指定工況的理想煞車比為 N_front : N_rear；並檢查 mu_w 與後軸離地限制。
沿用 Brake_ratio，在可達上限內取 10 點，將後軸力對前軸力作通過原點的最小平方擬合：
    k = sum(B_front * B_rear) / sum(B_front**2)
    beta_front = 1 / (1 + k), beta_rear = 1 - beta_front
指定 2 g 的理想分配、可達極限工況分配與掃描擬合固定比各自列出。
煞車機構整體等效機械利益使用指定煞車工況的最大總需求力：
    B_total_required = B_front + B_rear
    brake_mechanical_advantage = B_total_required / brake_driver_force_N
車手腳力初值為 500 N；此倍率以四輪接地總煞車力為輸出力。
所有分析計算後印出結果，並自動更新同資料夾的 vehicle_initial_sizing_report.md，不繪圖。
"""

import math
from pathlib import Path

from vehicle_initial_sizing_report import write_markdown_report


DEFAULT_REPORT_PATH = Path(__file__).with_name("vehicle_initial_sizing_report.md")


# 可直接修改以下參數；初值參考目前專案設定與 COG 計算結果。
# 本腳本只使用這裡的數值，不自動讀取 CSV 或執行其他分析。

# 懸吊配置
use_tender = True              # 是否使用 Tender；False：跳過 Heave 反算，直接使用原 Heave 主簧剛性

# 初始layout 設定
ms = 260.55                    # 全車簧上質量，kg 
mu = 14.4                      # 單輪簧下質量，kg（四輪平均）
h_cog = 0.3                    # 重心離地高度，m
lf = 0.765                     # 重心到前軸的縱向距離，m
lr = 0.765                     # 重心到後軸的縱向距離，m

# 性能目標
ax = 2.0                       # 縱向加速度，g；正值加速、負值煞車，剛性需求取絕對值
ay = 2.2                       # 側向加速度，g；正值右輪增載，剛性需求取絕對值
a_acc = 1.2                    # Gear_rate 無空力直線加速目標，g；該工況 ax = a_acc、ay = 0
# Anti-Scrub 沿用上述 ax = 2 g、a_acc = 1.2 g：anti_scrub = anti_dive * a_acc / ax。
brake_ax = ax                  # Brake_ratio 減速度大小，g；車身座標 ax = -brake_ax，ay = 0
target_lap_time_s = 5.0         # Skidpad 目標單圈時間，s（4.0～6.0）
drive_target_speed_kmh = 110.0  # 目標極速，km/h

# 規則與統計資料尺寸
L = lf + lr                    # 軸距由兩段距離相加，m（初值 1.53；規則最小值 1.525）
sus_travel = 0.025             # 目標懸吊壓縮行程，m 大於 0 規則設定行程須滿足（25 mm）
tf = 1.250                     # 前輪距，m（1250 mm）統計資料
tr = 1.240                     # 後輪距，m（1240 mm）統計資料
t = tf                         # 既有傾斜角與壓縮行程分析使用前輪距，m

# 空力參數
A_air = 1.0                    # 空力有效面積，m^2
air_density_kg_per_m3 = 1.225   # 空氣密度，kg/m^3；沿用 analysis/Aero_Cl_Cd.py

# 依照RCVD建議 之後再調整
kf = 0.55                      # 前軸剛性比例，kf:kr = 55:45
kr = 0.45                      # 後軸剛性比例

target_pitch_angle_deg = 1.0    # 允許俯仰角，deg（0.1～3.0）
target_roll_angle_deg = 2.0     # 允許側傾角，deg（0.1～3.0）

# Camber 歸零反解；由最小轉彎半徑求需求轉角，沿用已確認的正方向與固定座標負號。
kpi_deg = 8.0                  # 主銷內傾角，deg
min_turn_radius_m = 3.0        # 最小轉彎半徑，m；依 R = L/tan(theta) 計算單軌等效前輪轉角
caster_direction_check_deg = 10.0  # 僅用於印出 ±轉向角的方向驗證，不參與求解或修改轉向設定

MR = 1.0                       # 運動比；輪率 Kw = Ks * MR**2
sprung_roll_inertia_kg_m2 = 7.917820044730256  # 簧上 CG 的 Ixx；初值取 data/results/cog_movable/result.csv
# 臨界阻尼的彈簧與阻尼器均沿用 MR；上述慣量為手動初值，不自動重新讀取 COG 結果。

# 輪胎資料
Kt = 80000.0                   # 單輪輪胎垂直剛性，N/m
wl_mu_y = 1.81526957993174      # 橫向輪胎摩擦係數，初值沿用現有摩擦係數分析結果
mu_w = 1.6046564575663345       # 縱向輪胎摩擦係數；初值取目前 coefficient_of_friction 結果
R_tire = 0.2                   # 輪胎有效滾動半徑，m

# 傳動參數；轉速與車速初值沿用目前儲存設定，扭矩初值取既有馬達曲線峰值。
drive_motor_torque_Nm = 22.30565254  # 單顆馬達最大扭矩，Nm；本腳本手動設定、不自動讀取曲線
drive_motor_rpm = 15000.0       # 馬達最高轉速，rpm

# 經驗參數
N = 5.0                        # 與 Frequency vs mass 相同：目標簧上頻率 = 目前簧下頻率 / N
rc_chassis_stiffness_ratio = 10.0  # Kc / Ks，前 Roll Center 與 Anti dive 共用；車體剛性為懸吊的 10 倍
F_ref_ratio = 1.0              # Tender 與輪載使用所需下壓力的比例（0～1；1 為全部）
wl_aero_front_ratio = 0.5      # 輪載計算的空力前軸分配比例（0～1）；後軸為 1 減此值
cg_safety_factor = 1.0         # CG 傾斜幾何安全係數，至少為 1，沿用目前專案設定
brake_driver_force_N = 500.0    # 車手施加於煞車踏板的腳力，N

g = 9.81                       # 重力加速度，m/s^2


def calculate_weight_distribution(front_distance, rear_distance):
    """由重心到前後軸的縱向距離，回傳前、後軸靜態重量比例。"""
    for name, value in (("front_distance", front_distance), ("rear_distance", rear_distance)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} 必須為大於 0 的有限數值（m）")
    wheelbase = front_distance + rear_distance
    if not math.isfinite(wheelbase):
        raise ValueError("重心到前後軸的距離總和必須為有限數值（m）")

    return rear_distance / wheelbase, front_distance / wheelbase


def calculate_stiffness(mass, acceleration_g, height, span, angle_deg):# 角度剛性計算
    """回傳指定角度所需的等效剛性（N/m）與半幅位移（m）。"""
    for name, value in (("mass", mass), ("height", height), ("span", span)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} 必須為大於 0 的有限數值")
    if not math.isfinite(acceleration_g) or acceleration_g < 0:
        raise ValueError("acceleration_g 必須為大於或等於 0 的有限數值")
    if not math.isfinite(angle_deg) or not 0.1 <= angle_deg <= 3.0:
        raise ValueError("angle_deg 必須介於 0.1 與 3.0 度之間")

    displacement = (span / 2) * math.radians(angle_deg)
    moment = mass * acceleration_g * g * height
    equivalent_force = moment / (span / 2)
    stiffness = equivalent_force / (2 * displacement)
    return stiffness, displacement


def calculate_compressed_travel(mass, acceleration_g, height, span, travel):
    """回傳指定壓縮行程所需的等效剛性（N/m）與車身角度（deg）。"""
    for name, value in (("mass", mass), ("height", height), ("span", span)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} 必須為大於 0 的有限數值")
    if not math.isfinite(acceleration_g) or acceleration_g < 0:
        raise ValueError("acceleration_g 必須為大於或等於 0 的有限數值")
    if not math.isfinite(travel) or not 0 < travel <= 0.050:
        raise ValueError("travel 必須大於 0 且不超過 0.050 m")

    load_transfer = mass * acceleration_g * g * height / span
    stiffness = load_transfer / travel
    angle_deg = math.degrees(math.atan(2 * travel / span))
    return stiffness, angle_deg


def calculate_natural_frequency(mass, stiffness):
    """以全車簧上質量的一半與等效剛性（N/m）計算自然頻率（Hz）。"""
    for name, value in (("mass", mass), ("stiffness", stiffness)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} 必須為大於 0 的有限數值")

    effective_mass = mass / 2
    return math.sqrt(stiffness / effective_mass) / (2 * math.pi)


def calculate_spring_rate(motion_ratio, target_ride_rate, tire_stiffness):
    """由目標 ride rate 反算計入輪胎柔度後的彈簧剛性（N/m）。"""
    for name, value in (("motion_ratio", motion_ratio),
                        ("target_ride_rate", target_ride_rate),
                        ("tire_stiffness", tire_stiffness)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} 必須為大於 0 的有限數值")
    if target_ride_rate >= tire_stiffness:
        raise ValueError("目標 ride rate 必須小於輪胎剛性，才能反算彈簧剛性")

    wheel_rate = target_ride_rate * tire_stiffness / (tire_stiffness - target_ride_rate)
    return wheel_rate / motion_ratio**2


def calculate_tire_stiffness(motion_ratio, tire_stiffness, pitch_stiffness, roll_stiffness):
    """回傳一般、Pitch、Roll 彈簧剛性及一般 Ks 的目標／實際 ride rate。"""
    pitch_spring = calculate_spring_rate(motion_ratio, pitch_stiffness, 2 * tire_stiffness)
    roll_spring = calculate_spring_rate(motion_ratio, roll_stiffness, 2 * tire_stiffness)
    target_ride_rate = (roll_stiffness + pitch_stiffness) / 4

    def ride_rate(spring_stiffness):
        wheel_rate = spring_stiffness * motion_ratio**2
        return wheel_rate * tire_stiffness / (wheel_rate + tire_stiffness)

    spring_min, spring_max, samples = 20_000, 80_000, 2_000
    spring_range = (
        spring_min + index * (spring_max - spring_min) / (samples - 1)
        for index in range(samples)
    )
    selected_spring = min(spring_range, key=lambda spring: abs(ride_rate(spring) - target_ride_rate))
    return {
        "Ks": selected_spring,
        "Ks_pitch_N_per_m": pitch_spring,
        "Ks_roll_N_per_m": roll_spring,
        "target_ride_rate_N_per_m": target_ride_rate,
        "actual_ride_rate_N_per_m": ride_rate(selected_spring),
    }


def calculate_frequency_vs_mass(mass, unsprung_mass, motion_ratio, tire_stiffness,
                                pitch_spring, roll_spring):
    """以全車簧上質量與單輪簧下質量，估算四分之一車的兩個自然頻率。"""
    for name, value in (("mass", mass), ("unsprung_mass", unsprung_mass),
                        ("motion_ratio", motion_ratio), ("tire_stiffness", tire_stiffness),
                        ("pitch_spring", pitch_spring), ("roll_spring", roll_spring)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} 必須為大於 0 的有限數值")

    total_mass = mass + 4 * unsprung_mass
    quarter_sprung_mass = mass / 4
    quarter_total_mass = quarter_sprung_mass + unsprung_mass
    equivalent_spring = (roll_spring + pitch_spring) / 4
    wheel_rate = equivalent_spring * motion_ratio**2
    ride_rate = wheel_rate * tire_stiffness / (wheel_rate + tire_stiffness)
    sprung_frequency = math.sqrt(ride_rate / quarter_sprung_mass) / (2 * math.pi)
    unsprung_frequency = math.sqrt((tire_stiffness + wheel_rate) / unsprung_mass) / (2 * math.pi)

    return {
        "m_total_vehicle_kg": total_mass,
        "quarter_sprung_mass_kg": quarter_sprung_mass,
        "unsprung_mass_ratio_target_percent": unsprung_mass / quarter_total_mass * 100,
        "equivalent_spring_stiffness_N_per_m": equivalent_spring,
        "wheel_rate_N_per_m": wheel_rate,
        "ride_rate_N_per_m": ride_rate,
        "frequency_sprung_target_Hz": sprung_frequency,
        "frequency_unsprung_target_Hz": unsprung_frequency,
    }


def calculate_heave_reduction(mass, unsprung_mass, motion_ratio, tire_stiffness,
                              pitch_spring, roll_spring, frequency_divisor):
    """沿用 Frequency vs mass，以目前簧下頻率 / N 為目標反算 heave 剛性。"""
    if not math.isfinite(frequency_divisor) or frequency_divisor <= 0:
        raise ValueError("frequency_divisor（N）必須為大於 0 的有限數值")
    current = calculate_frequency_vs_mass(
        mass, unsprung_mass, motion_ratio, tire_stiffness, pitch_spring, roll_spring
    )
    target_frequency = current['frequency_unsprung_target_Hz'] / frequency_divisor
    result = {
        "target_natural_frequency_Hz": target_frequency,
        "current_sprung_frequency_Hz": current['frequency_sprung_target_Hz'],
        "current_unsprung_frequency_Hz": current['frequency_unsprung_target_Hz'],
        "can_reach_target": False,
        "Ks_required_target_frequency_N_per_m": None,
        "Ks_scale_target_frequency": None,
        "heave_stiffness_reduction_N_per_m": None,
        "heave_stiffness_reduction_percent": None,
        "adjusted_sprung_frequency_Hz": None,
        "adjusted_unsprung_frequency_Hz": None,
    }
    required_ride_rate = (2 * math.pi * target_frequency)**2 * (mass / 4)
    if required_ride_rate >= tire_stiffness:
        result['reason'] = "目標頻率所需的 ride rate 不小於輪胎剛性 Kt，無有限正剛性解。"
        return result

    required_equivalent_spring = calculate_spring_rate(
        motion_ratio, required_ride_rate, tire_stiffness
    )
    required_heave = 4 * required_equivalent_spring - roll_spring
    if required_heave <= 0:
        result['reason'] = "目標頻率過低；固定目前 Roll 剛性時，沒有正的 heave 剛性可達成。"
        return result

    adjusted = calculate_frequency_vs_mass(
        mass, unsprung_mass, motion_ratio, tire_stiffness, required_heave, roll_spring
    )
    result.update({
        "can_reach_target": True,
        "Ks_required_target_frequency_N_per_m": required_heave,
        "Ks_scale_target_frequency": required_heave / pitch_spring,
        "heave_stiffness_reduction_N_per_m": pitch_spring - required_heave,
        "heave_stiffness_reduction_percent": (1 - required_heave / pitch_spring) * 100,
        "adjusted_sprung_frequency_Hz": adjusted['frequency_sprung_target_Hz'],
        "adjusted_unsprung_frequency_Hz": adjusted['frequency_unsprung_target_Hz'],
    })
    return result


def calculate_tender_stiffness(main_heave_stiffness, target_stiffness_scale):
    """反算目標串聯 Tender 剛性與加入 Tender 後的等效 Heave 剛性。"""
    if not math.isfinite(main_heave_stiffness) or main_heave_stiffness <= 0:
        raise ValueError("主 heave 彈簧剛性必須為大於 0 的有限數值（N/m）")
    if not math.isfinite(target_stiffness_scale) or not 0 < target_stiffness_scale < 1:
        raise ValueError("目標剛性倍率必須介於 0 與 1 之間，才有有限正的串聯 tender 剛性")

    target_series = main_heave_stiffness * target_stiffness_scale
    tender_stiffness = target_series * main_heave_stiffness / (main_heave_stiffness - target_series)
    combined_heave = main_heave_stiffness * tender_stiffness / (main_heave_stiffness + tender_stiffness)
    return {
        "K_heave_main_N_per_m": main_heave_stiffness,
        "K_tender_required_N_per_m": tender_stiffness,
        "tender_to_heave_stiffness_ratio": tender_stiffness / main_heave_stiffness,
        "K_series_target_N_per_m": target_series,
        "K_heave_with_tender_N_per_m": combined_heave,
    }


def calculate_critical_damping(effective_mass, stiffness):
    """線性單自由度臨界阻尼，質量 kg、剛性 N/m，回傳 N s/m。"""
    for name, value in (("effective_mass", effective_mass), ("stiffness", stiffness)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} 必須為大於 0 的有限數值")
    return 2 * math.sqrt(effective_mass * stiffness)


def calculate_suspension_critical_damping(sprung_mass, front_weight_ratio,
                                         front_roll_spring, rear_roll_spring,
                                         main_heave_spring, series_heave_spring,
                                         motion_ratio, front_track, rear_track, sprung_roll_inertia):
    """前後單支阻尼器的 SDOF 臨界參考；Roll 依剛性比例分配整車臨界角阻尼。"""
    for name, value in (("sprung_mass", sprung_mass), ("front_roll_spring", front_roll_spring),
                        ("rear_roll_spring", rear_roll_spring), ("main_heave_spring", main_heave_spring),
                        ("motion_ratio", motion_ratio), ("front_track", front_track),
                        ("rear_track", rear_track), ("sprung_roll_inertia", sprung_roll_inertia)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} 必須為大於 0 的有限數值")
    if not math.isfinite(front_weight_ratio) or not 0 < front_weight_ratio < 1:
        raise ValueError("front_weight_ratio 必須為介於 0 與 1 之間的有限比例")
    if series_heave_spring is not None:
        if not math.isfinite(series_heave_spring) or not 0 < series_heave_spring < main_heave_spring:
            raise ValueError("series_heave_spring 必須為低於主簧的有限正剛性，或為 None")

    roll_stiffness = {
        "front": front_roll_spring * (motion_ratio * front_track)**2,
        "rear": rear_roll_spring * (motion_ratio * rear_track)**2,
    }
    total_roll_stiffness = sum(roll_stiffness.values())
    total_roll_critical = 2 * math.sqrt(total_roll_stiffness * sprung_roll_inertia)
    roll = {}
    for axle, spring, track in (("front", front_roll_spring, front_track),
                                ("rear", rear_roll_spring, rear_track)):
        fraction = roll_stiffness[axle] / total_roll_stiffness
        angular_damping = total_roll_critical * fraction
        roll[axle] = {
            "spring_stiffness_N_per_m": spring,
            "angular_stiffness_Nm_per_rad": roll_stiffness[axle],
            "stiffness_fraction": fraction,
            "angular_damping_Nms_per_rad": angular_damping,
            "damper_critical_damping_Ns_per_m": angular_damping / (motion_ratio * track)**2,
        }

    result = {
        "roll_total_stiffness_Nm_per_rad": total_roll_stiffness,
        "roll_total_critical_damping_Nms_per_rad": total_roll_critical,
        "roll": roll,
    }
    for mode, spring in (("heave_with_tender", series_heave_spring), ("pure_heave", main_heave_spring)):
        if spring is None:
            result[mode] = None
            continue
        body_stiffness = spring * motion_ratio**2
        result[mode] = {}
        for axle, fraction in (("front", front_weight_ratio), ("rear", 1 - front_weight_ratio)):
            mass = sprung_mass * fraction
            critical = calculate_critical_damping(mass, body_stiffness)
            result[mode][axle] = {
                "sprung_mass_kg": mass,
                "spring_stiffness_N_per_m": spring,
                "body_stiffness_N_per_m": body_stiffness,
                "body_critical_damping_Ns_per_m": critical,
                "damper_critical_damping_Ns_per_m": critical / motion_ratio**2,
            }
    return result


def calculate_rate_chain(spring_rate, motion_ratio, tire_stiffness, sprung_mass_per_wheel):
    """單輪等效 Ks → Kw → Kr，分別用對應座標質量求頻率及 SDOF 臨界阻尼。"""
    for name, value in (("spring_rate", spring_rate), ("motion_ratio", motion_ratio),
                        ("tire_stiffness", tire_stiffness), ("sprung_mass_per_wheel", sprung_mass_per_wheel)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} 必須為大於 0 的有限數值")
    wheel_rate = spring_rate * motion_ratio**2
    ride_rate = wheel_rate * tire_stiffness / (wheel_rate + tire_stiffness)
    spring_coordinate_mass = sprung_mass_per_wheel / motion_ratio**2
    return {
        "spring_rate_N_per_m": spring_rate,
        "wheel_rate_N_per_m": wheel_rate,
        "ride_rate_N_per_m": ride_rate,
        "sprung_mass_per_wheel_kg": sprung_mass_per_wheel,
        "spring_coordinate_mass_kg": spring_coordinate_mass,
        "frequency_Ks_Hz": math.sqrt(spring_rate / spring_coordinate_mass) / (2 * math.pi),
        "frequency_Kw_Hz": math.sqrt(wheel_rate / sprung_mass_per_wheel) / (2 * math.pi),
        "frequency_Kr_Hz": math.sqrt(ride_rate / sprung_mass_per_wheel) / (2 * math.pi),
        "critical_damping_Ks_Ns_per_m": calculate_critical_damping(spring_coordinate_mass, spring_rate),
        "critical_damping_Kw_Ns_per_m": calculate_critical_damping(sprung_mass_per_wheel, wheel_rate),
        "critical_damping_Kr_Ns_per_m": calculate_critical_damping(sprung_mass_per_wheel, ride_rate),
    }


def calculate_rate_cases(sprung_mass, front_weight_ratio, motion_ratio, tire_stiffness,
                         front_roll_spring, rear_roll_spring, main_heave_spring, series_heave_spring):
    """前後四組 Ks；series_heave_spring 接本次 Heave 剛性（關閉 Tender 時為主簧）。"""
    for name, value in (("sprung_mass", sprung_mass), ("front_roll_spring", front_roll_spring),
                        ("rear_roll_spring", rear_roll_spring), ("main_heave_spring", main_heave_spring)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} 必須為大於 0 的有限數值")
    if not math.isfinite(front_weight_ratio) or not 0 < front_weight_ratio < 1:
        raise ValueError("front_weight_ratio 必須為介於 0 與 1 之間的有限比例")
    if series_heave_spring is not None and (not math.isfinite(series_heave_spring) or series_heave_spring <= 0):
        raise ValueError("series_heave_spring 必須為有限正值或 None")
    result = {}
    for axle, fraction, roll_spring in (("front", front_weight_ratio, front_roll_spring),
                                        ("rear", 1 - front_weight_ratio, rear_roll_spring)):
        mass = sprung_mass * fraction / 2
        rates = {
            "combined_average": (series_heave_spring + roll_spring) / 2
                                if series_heave_spring is not None else None,
            "heave_with_tender": series_heave_spring,  # 保留結果欄名；此列使用本次 Heave 剛性
            "roll": roll_spring,
            "heave_only": main_heave_spring,
        }
        result[axle] = {name: calculate_rate_chain(rate, motion_ratio, tire_stiffness, mass)
                       if rate is not None else None for name, rate in rates.items()}
    return result


def calculate_roll_pitch_gradients(total_mass, cog_height, front_distance, rear_distance,
                                   front_track, rear_track, motion_ratio, tire_stiffness,
                                   front_roll_spring, rear_roll_spring, main_heave_spring,
                                   series_heave_spring, front_roll_center, rear_roll_center, anti_dive=0.):
    """準靜態小角度 gradient（deg/g）；Roll 沿用 HL 的 RC 力臂與輪胎串聯模型。"""
    for name, value in (("total_mass", total_mass), ("front_track", front_track), ("rear_track", rear_track),
                        ("motion_ratio", motion_ratio), ("tire_stiffness", tire_stiffness),
                        ("front_roll_spring", front_roll_spring), ("rear_roll_spring", rear_roll_spring),
                        ("main_heave_spring", main_heave_spring)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} 必須為大於 0 的有限數值")
    for name, value in (("cog_height", cog_height), ("front_roll_center", front_roll_center),
                        ("rear_roll_center", rear_roll_center)):
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"{name} 必須為非負有限數值（m）")
    if not math.isfinite(anti_dive) or not 0 <= anti_dive <= 1:
        raise ValueError("anti_dive 必須為介於 0 與 1 之間的有限比例")
    if series_heave_spring is not None and (not math.isfinite(series_heave_spring) or series_heave_spring <= 0):
        raise ValueError("series_heave_spring 必須為有限正值或 None")
    wf, wr = calculate_weight_distribution(front_distance, rear_distance)
    wheelbase = front_distance + rear_distance
    roll_axis_height = wf * front_roll_center + wr * rear_roll_center
    roll_lever = cog_height - roll_axis_height
    roll_suspension, roll_ride = 0., 0.
    for spring, track in ((front_roll_spring, front_track), (rear_roll_spring, rear_track)):
        suspension = spring * (motion_ratio * track)**2
        tire = tire_stiffness * track**2 / 2
        roll_suspension += suspension
        roll_ride += suspension * tire / (suspension + tire)
    roll_moment_per_g = total_mass * g * roll_lever
    result = {
        "roll_axis_height_at_cg_m": roll_axis_height,
        "roll_moment_arm_m": roll_lever,
        "roll_suspension_stiffness_Nm_per_rad": roll_suspension,
        "roll_ride_stiffness_Nm_per_rad": roll_ride,
        "roll_gradient_suspension_deg_per_g": math.degrees(roll_moment_per_g / roll_suspension),
        "roll_gradient_with_tires_deg_per_g": math.degrees(roll_moment_per_g / roll_ride),
        "pitch": {},
    }
    pitch_moment_per_g = total_mass * g * cog_height
    pitch_tire_stiffness = tire_stiffness * wheelbase**2
    tire_gradient = math.degrees(pitch_moment_per_g / pitch_tire_stiffness)
    for mode, spring in (("heave_with_tender", series_heave_spring), ("heave_only", main_heave_spring)):
        if spring is None:
            result['pitch'][mode] = None
            continue
        axle_rate = spring * motion_ratio**2
        pitch_stiffness = axle_rate * wheelbase**2 / 2
        suspension_gradient = math.degrees(pitch_moment_per_g / pitch_stiffness)
        result['pitch'][mode] = {
            "pitch_suspension_stiffness_Nm_per_rad": pitch_stiffness,
            "pitch_tire_stiffness_Nm_per_rad": pitch_tire_stiffness,
            "gradient_suspension_deg_per_g": suspension_gradient,
            "gradient_with_tires_deg_per_g": suspension_gradient + tire_gradient,
            "gradient_with_tires_and_anti_dive_deg_per_g": (1 - anti_dive) * suspension_gradient + tire_gradient,
        }
    return result


def calculate_anti_dive(chassis_stiffness_ratio):
    """依車體與懸吊剛性說明的解析解，求懸吊路徑與 Anti dive 比例。"""
    if not math.isfinite(chassis_stiffness_ratio) or chassis_stiffness_ratio <= 0:
        raise ValueError("chassis_stiffness_ratio 必須為大於 0 的有限數值")

    anti_dive = 1 / (1 + chassis_stiffness_ratio)
    suspension_fraction = chassis_stiffness_ratio / (1 + chassis_stiffness_ratio)
    return {
        "anti_dive": anti_dive,
        "anti_dive_percent": anti_dive * 100,
        "anti_dive_suspension_fraction": suspension_fraction,
        "anti_dive_normalized_min_stiffness": suspension_fraction,
    }


def calculate_anti_scrub(anti_dive, acceleration_g, reference_acceleration_g):
    """依指定公式 anti_dive * a_acc / ax 計算 Anti-Scrub；兩加速度均用 g。"""
    if not math.isfinite(anti_dive) or not 0 <= anti_dive <= 1:
        raise ValueError("anti_dive 必須為介於 0 與 1 之間的有限比例")
    if not math.isfinite(acceleration_g) or acceleration_g < 0:
        raise ValueError("acceleration_g（a_acc）必須為大於或等於 0 的有限數值")
    if not math.isfinite(reference_acceleration_g) or reference_acceleration_g == 0:
        raise ValueError("reference_acceleration_g（ax）必須為非零的有限數值")
    anti_scrub = anti_dive * acceleration_g / reference_acceleration_g
    return {
        "anti_scrub": anti_scrub,
        "anti_scrub_percent": anti_scrub * 100,
    }


def calculate_roll_center(cog_height, chassis_stiffness_ratio):
    """直接使用解析解，回傳懸吊路徑比例、正規化最小剛性與 RC 高度。"""
    for name, value in (("cog_height", cog_height),
                        ("chassis_stiffness_ratio", chassis_stiffness_ratio)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} 必須為大於 0 的有限數值")

    optimal_ratio = 1 / (1 + chassis_stiffness_ratio)
    minimum_stiffness = chassis_stiffness_ratio / (1 + chassis_stiffness_ratio)

    return {
        "rc_normalized_optimal_ratio": optimal_ratio,
        "rc_normalized_min_stiffness": minimum_stiffness,
        "rc_suspension_fraction": minimum_stiffness,
        "rc_normalized_optimal_height_m": optimal_ratio * cog_height,
    }


def calculate_rear_roll_center(front_height, wf, wr, tf, tr, kf, kr):
    """依 h_rear = h_front * (wf/wr) * (tr/tf) * (kf/kr) 計算後 RC 高度（m）。"""
    if not math.isfinite(front_height) or front_height < 0:
        raise ValueError("front_height 必須為大於或等於 0 的有限數值（m）")
    for name, value in (("wf", wf), ("wr", wr), ("tf", tf),
                        ("tr", tr), ("kf", kf), ("kr", kr)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} 必須為大於 0 的有限數值")

    return front_height * (wf / wr) * (tr / tf) * (kf / kr)


def calculate_fvsa(travel_m, track_m):
    """依指定 FVSA 過程計算；固定以 m 代入，camber gain 按 1 m 位移換算。"""
    for name, value in (("travel_m", travel_m), ("track_m", track_m)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} 必須為大於 0 的有限數值（m）")

    roll_angle_rad = math.atan(2 * travel_m / track_m)
    fvsa_tangent = math.tan(roll_angle_rad / (2 * travel_m))
    if not math.isfinite(fvsa_tangent) or fvsa_tangent <= 0:
        raise ValueError("指定 FVSA 公式在這組公尺制參數下無法得到有限正長度")
    fvsa_length_m = 1 / fvsa_tangent
    if not math.isfinite(fvsa_length_m):
        raise ValueError("FVSA 計算值必須為有限數值")
    camber_change_rad = math.atan(1 / fvsa_length_m)
    camber_gain_deg_per_m = math.degrees(camber_change_rad)
    return {
        "max_roll_angle_rad": roll_angle_rad,
        "max_roll_angle_deg": math.degrees(roll_angle_rad),
        "fvsa_length_m": fvsa_length_m,
        "fvsa_length_mm": fvsa_length_m * 1000,
        "camber_change_rad_per_m": camber_change_rad,
        "camber_gain_deg_per_m": camber_gain_deg_per_m,
        "camber_gain_deg_per_mm": camber_gain_deg_per_m / 1000,
        "max_camber_change_deg": camber_gain_deg_per_m * travel_m,
    }


def calculate_skidpad_downforce(mass, unsprung_mass, tire_friction, target_lap_time):
    """沿用 skidpad_test，以全車簧上質量、單輪簧下質量及圈速反算整車下壓力。"""
    for name, value in (("mass", mass), ("unsprung_mass", unsprung_mass),
                        ("tire_friction", tire_friction)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} 必須為大於 0 的有限數值")
    if not math.isfinite(target_lap_time) or not 4.0 <= target_lap_time <= 6.0:
        raise ValueError("target_lap_time 必須介於 4.0 與 6.0 秒之間")

    total_mass = mass + 4 * unsprung_mass
    diameter = 18.25
    factor = 1.4
    radius = diameter / 2
    speed = math.pi * diameter / target_lap_time
    speed_kmh = speed * 3.6
    lateral_acceleration = speed**2 / radius
    required_mu = lateral_acceleration / g * factor
    downforce = (required_mu / tire_friction - 1) * total_mass * g
    return {
        "F_ref": downforce,
        "v_ref": speed_kmh,
        "skidpad_target_lap_time_s": target_lap_time,
        "skidpad_target_downforce_N": downforce,
        "skidpad_target_required_mu": required_mu,
        "skidpad_total_mass_kg": total_mass,
        "skidpad_diameter_m": diameter,
        "skidpad_safety_factor": factor,
        "skidpad_target_speed_m_per_s": speed,
        "skidpad_target_lateral_acceleration_m_per_s2": lateral_acceleration,
        "skidpad_required_aero_downforce_N": max(0.0, downforce),
    }


def calculate_aero_lift_coefficient(required_downforce_N, speed_m_per_s, effective_area_m2, air_density):
    """依 F=C*rho*A*v^2 反解目標 C，另列原 Aero_Cl_Cd 定義的 Cl；下壓力為正。"""
    if not math.isfinite(required_downforce_N) or required_downforce_N < 0:
        raise ValueError("required_downforce_N 必須為非負的有限數值（N）")
    for name, value in (("speed_m_per_s", speed_m_per_s), ("effective_area_m2", effective_area_m2),
                        ("air_density", air_density)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} 必須為大於 0 的有限數值")
    coefficient = required_downforce_N / (air_density * effective_area_m2 * speed_m_per_s**2)
    return {
        "target_coefficient_C": coefficient,
        "standard_downforce_coefficient_Cl": 2 * coefficient,
    }


def calculate_tender_compression(main_heave_stiffness, tender_to_heave_ratio,
                                 reference_downforce, reference_downforce_ratio=1.0):
    """沿用 Tender 無煞車工況，計算目標下壓力時每組彈簧的壓縮與壓實設計行程。"""
    for name, value in (("main_heave_stiffness", main_heave_stiffness),
                        ("tender_to_heave_ratio", tender_to_heave_ratio)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} 必須為大於 0 的有限數值")
    if not math.isfinite(reference_downforce) or reference_downforce < 0:
        raise ValueError("reference_downforce 必須為大於或等於 0 的有限數值（N）")
    if not math.isfinite(reference_downforce_ratio) or not 0 <= reference_downforce_ratio <= 1:
        raise ValueError("reference_downforce_ratio 必須介於 0 與 1 之間")

    main_rate_N_per_mm = main_heave_stiffness / 1000
    tender_rate_N_per_mm = main_rate_N_per_mm * tender_to_heave_ratio
    applied_downforce = reference_downforce * reference_downforce_ratio
    assembly_force = applied_downforce / 2
    main_compression = assembly_force / main_rate_N_per_mm
    tender_compression = assembly_force / tender_rate_N_per_mm
    total_compression = main_compression + tender_compression
    return {
        "tender_bind_vehicle_downforce_N": applied_downforce,
        "tender_bind_force_N": assembly_force,
        "main_spring_compression_mm": main_compression,
        "tender_bind_spring_stroke_mm": tender_compression,
        "tender_bind_total_stroke_mm": total_compression,
        "front_compression_mm": total_compression,
        "rear_compression_mm": total_compression,
        "heave_mm": total_compression,
    }


def calculate_lateral_tire_roll(axle_mass, cog_height, track, tire_stiffness, acceleration_y_g):
    """純 ay 的單軸左右輪力矩平衡與輪胎壓縮；負輪載時只保留線性外推。"""
    for name, value in (("axle_mass", axle_mass), ("track", track),
                        ("tire_stiffness", tire_stiffness)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} 必須為大於 0 的有限數值")
    if not math.isfinite(cog_height) or cog_height < 0:
        raise ValueError("cog_height 必須為大於或等於 0 的有限數值（m）")
    if not math.isfinite(acceleration_y_g):
        raise ValueError("acceleration_y_g 必須為有限數值（g）")

    lateral_force = axle_mass * acceleration_y_g * g
    roll_moment = lateral_force * cog_height
    weight = axle_mass * g
    transfer = roll_moment / track
    left_load = weight / 2 - transfer
    right_load = weight / 2 + transfer
    static_compression = weight / (2 * tire_stiffness)
    left_compression = left_load / tire_stiffness
    right_compression = right_load / tire_stiffness
    deformation_difference = right_compression - left_compression
    linear_roll = deformation_difference / track
    force_tolerance = 1e-12 * max(weight, 1.0)
    contact_valid = min(left_load, right_load) >= -force_tolerance
    at_lift_boundary = math.isclose(min(left_load, right_load), 0.0, abs_tol=force_tolerance)
    return {
        "axle_mass_kg": axle_mass,
        "lateral_force_N": lateral_force,
        "roll_moment_Nm": roll_moment,
        "axle_weight_N": weight,
        "left_normal_load_N": left_load,
        "right_normal_load_N": right_load,
        "normal_load_difference_N": right_load - left_load,
        "lateral_load_transfer_N": transfer,
        "static_compression_m": static_compression,
        "left_linear_compression_m": left_compression,
        "right_linear_compression_m": right_compression,
        "left_compression_change_m": -transfer / tire_stiffness,
        "right_compression_change_m": transfer / tire_stiffness,
        "deformation_difference_m": deformation_difference,
        "linear_tire_roll_angle_rad": linear_roll,
        "linear_tire_roll_angle_deg": math.degrees(linear_roll),
        "tire_roll_angle_rad": linear_roll if contact_valid else None,
        "tire_roll_angle_deg": math.degrees(linear_roll) if contact_valid else None,
        "contact_valid": contact_valid,
        "at_lift_boundary": at_lift_boundary,
        "ay_contact_limit_g": track / (2 * cog_height) if cog_height > 0 else math.inf,
    }


def calculate_required_steering_angle(wheelbase_m, minimum_radius_m):
    """由 R=L/tan(theta) 求最大需求單軌等效前輪轉角（正角度，deg）。"""
    for name, value in (("wheelbase_m", wheelbase_m), ("minimum_radius_m", minimum_radius_m)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} 必須為大於 0 的有限數值（m）")
    return math.degrees(math.atan(wheelbase_m / minimum_radius_m))


def calculate_steering_camber(caster_deg, kpi_deg, steering_angle_deg):
    """原式的有號 Camber 變化（deg）；只做角度單位換算，不套用輪側方向修正。"""
    for name, value in (("caster_deg", caster_deg), ("kpi_deg", kpi_deg),
                        ("steering_angle_deg", steering_angle_deg)):
        if not math.isfinite(value):
            raise ValueError(f"{name} 必須為有限角度（deg）")
    delta = math.radians(steering_angle_deg)
    change = delta * math.sin(math.radians(caster_deg)) \
        - (1 - math.cos(delta)) * math.sin(math.radians(kpi_deg))
    return math.degrees(change)


def calculate_caster_for_zero_camber(roll_angle_deg, tire_roll_angle_deg,
                                     fvsa_camber_change_deg, kpi_deg, steering_angle_deg):
    """使用固定有號轉角與固定座標負號反解 Caster；不自動選方向或依結果正負變號。"""
    for name, value in (("roll_angle_deg", roll_angle_deg), ("tire_roll_angle_deg", tire_roll_angle_deg),
                        ("fvsa_camber_change_deg", fvsa_camber_change_deg),
                        ("kpi_deg", kpi_deg), ("steering_angle_deg", steering_angle_deg)):
        if not math.isfinite(value):
            raise ValueError(f"{name} 必須為有限角度（deg）")

    base_camber_deg = roll_angle_deg + tire_roll_angle_deg - fvsa_camber_change_deg
    if not math.isfinite(base_camber_deg):
        raise ValueError("轉向前 Camber 必須為有限角度")
    base_camber_rad = math.radians(base_camber_deg)
    delta = math.radians(steering_angle_deg)
    kpi_term = (1 - math.cos(delta)) * math.sin(math.radians(kpi_deg))
    result = {
        "base_camber_deg": base_camber_deg,
        "steering_angle_deg": steering_angle_deg,
        "kpi_deg": kpi_deg,
        "kpi_camber_change_deg": -math.degrees(kpi_term),
        "required_caster_sine": None,
        "solution_status": "unreachable",
        "has_real_solution": False,
        "caster_deg": None,
        "raw_steering_camber_change_deg": None,
        "camber_direction_factor": -1,
        "caster_camber_change_deg": None,
        "steering_camber_change_deg": None,
        "final_camber_deg": None,
        "reason": "",
    }
    if delta == 0:
        if math.isclose(base_camber_rad, 0., abs_tol=1e-12):
            result.update(solution_status="underdetermined", has_real_solution=True,
                          reason="delta = 0 且原 Camber 已為 0，無法決定唯一 Caster。")
        else:
            result["reason"] = "delta = 0，轉向不會產生 Camber 變化。"
        return result

    # gamma_final = gamma_base - [delta*sin(C) - (1-cos(delta))*sin(K)]。
    # delta 保留設定的正負號；整式前的負號是固定座標定義。
    sine = (base_camber_rad + kpi_term) / delta
    result["required_caster_sine"] = sine
    if not -1 - 1e-12 <= sine <= 1 + 1e-12:
        result["reason"] = "固定轉向角下所需 sin(caster) 超出 [-1, 1]，無實數解。"
        return result
    caster_rad = math.asin(max(-1., min(1., sine)))
    caster_deg = math.degrees(caster_rad)
    raw_change = calculate_steering_camber(caster_deg, kpi_deg, steering_angle_deg)
    applied_change = -raw_change
    residual = base_camber_deg + applied_change
    result.update({
        "solution_status": "solved",
        "has_real_solution": True,
        "caster_deg": caster_deg,
        "raw_steering_camber_change_deg": raw_change,
        "caster_camber_change_deg": math.degrees(delta * math.sin(caster_rad)),
        "steering_camber_change_deg": applied_change,
        "final_camber_deg": 0. if math.isclose(residual, 0., abs_tol=1e-10) else residual,
    })
    return result


def calculate_suspension_wheel_loads(mass, unsprung_mass, cog_height,
                                    front_distance, rear_distance, front_track, rear_track,
                                    acceleration_x_g, acceleration_y_g, downforce,
                                    aero_front_ratio, front_roll_stiffness, rear_roll_stiffness):
    """沿用 sus_load，回傳四輪原始法向載重；加速度用 g，Roll 剛性用 Nm/rad。"""
    for name, value in (("mass", mass), ("front_track", front_track), ("rear_track", rear_track),
                        ("front_roll_stiffness", front_roll_stiffness),
                        ("rear_roll_stiffness", rear_roll_stiffness)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} 必須為大於 0 的有限數值")
    for name, value in (("unsprung_mass", unsprung_mass), ("cog_height", cog_height),
                        ("downforce", downforce)):
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"{name} 必須為大於或等於 0 的有限數值")
    for name, value in (("acceleration_x_g", acceleration_x_g),
                        ("acceleration_y_g", acceleration_y_g)):
        if not math.isfinite(value):
            raise ValueError(f"{name} 必須為有限數值")
    if not math.isfinite(aero_front_ratio) or not 0 <= aero_front_ratio <= 1:
        raise ValueError("aero_front_ratio 必須介於 0 與 1 之間")

    front_ratio, rear_ratio = calculate_weight_distribution(front_distance, rear_distance)
    wheelbase = front_distance + rear_distance
    total_mass = mass + 4 * unsprung_mass
    longitudinal_transfer = total_mass * acceleration_x_g * g * cog_height / wheelbase
    front_load = total_mass * g * front_ratio + downforce * aero_front_ratio - longitudinal_transfer
    rear_load = total_mass * g * rear_ratio + downforce * (1 - aero_front_ratio) + longitudinal_transfer
    front_roll_fraction = front_roll_stiffness / (front_roll_stiffness + rear_roll_stiffness)
    roll_moment = total_mass * acceleration_y_g * g * cog_height
    front_transfer = front_roll_fraction * roll_moment / front_track
    rear_transfer = (1 - front_roll_fraction) * roll_moment / rear_track
    wheel_loads = {
        "FL": front_load / 2 - front_transfer,
        "FR": front_load / 2 + front_transfer,
        "RL": rear_load / 2 - rear_transfer,
        "RR": rear_load / 2 + rear_transfer,
    }
    return {
        "total_mass_kg": total_mass,
        "total_normal_load_N": total_mass * g + downforce,
        "front_axle_load_N": front_load,
        "rear_axle_load_N": rear_load,
        "longitudinal_transfer_N": longitudinal_transfer,
        "front_roll_fraction": front_roll_fraction,
        "front_lateral_transfer_N": front_transfer,
        "rear_lateral_transfer_N": rear_transfer,
        "wheel_loads_N": wheel_loads,
        "contact_valid": all(load >= 0 for load in wheel_loads.values()),
    }


def calculate_tire_force_demands(wheel_loads, total_mass, acceleration_x_g, acceleration_y_g):
    """依非負輪載占比分配 m*a 的需求力；負輪載時整組結果僅為參考。"""
    if not math.isfinite(total_mass) or total_mass <= 0:
        raise ValueError("total_mass 必須為大於 0 的有限數值（kg）")
    for name, value in (("acceleration_x_g", acceleration_x_g),
                        ("acceleration_y_g", acceleration_y_g)):
        if not math.isfinite(value):
            raise ValueError(f"{name} 必須為有限數值")
    normal_loads = {}
    for wheel in ("FL", "FR", "RL", "RR"):
        if not math.isfinite(wheel_loads[wheel]):
            raise ValueError(f"{wheel} 輪載必須為有限數值（N）")
        normal_loads[wheel] = max(wheel_loads[wheel], 0.0)
    total_normal_load = sum(normal_loads.values())
    if not math.isfinite(total_normal_load) or total_normal_load <= 0:
        raise ValueError("非負輪載總和必須為大於 0 的有限數值（N）")

    total_fx = total_mass * acceleration_x_g * g
    total_fy = total_mass * acceleration_y_g * g
    forces = {}
    for wheel, normal_load in normal_loads.items():
        fraction = normal_load / total_normal_load
        fx, fy = fraction * total_fx, fraction * total_fy
        forces[wheel] = {
            "raw_Fz_N": wheel_loads[wheel],
            "Fx_N": fx,
            "Fy_N": fy,
            "Fz_N": normal_load,
            "force_magnitude_N": math.hypot(fx, fy, normal_load),
            "load_fraction": fraction,
        }
    contact_valid = all(load >= 0 for load in wheel_loads.values())
    most_loaded = max(forces, key=lambda wheel: forces[wheel]['force_magnitude_N'])
    return {
        "wheel_forces": forces,
        "total_Fx_N": total_fx,
        "total_Fy_N": total_fy,
        "clipped_total_Fz_N": total_normal_load,
        "contact_valid": contact_valid,
        "reference_only": not contact_valid,
        "most_loaded_wheel": most_loaded,
    }


def calculate_gear_rate(mass, unsprung_mass, cog_height, front_distance, rear_distance,
                        acceleration_g, tire_radius, motor_torque, motor_rpm, target_speed_kmh):
    """無空力直線加速，沿用 Gear_rate 求每輪所需齒比、極速齒比及算術平均。"""
    for name, value in (("mass", mass), ("acceleration_g", acceleration_g),
                        ("tire_radius", tire_radius), ("motor_torque", motor_torque),
                        ("motor_rpm", motor_rpm), ("target_speed_kmh", target_speed_kmh)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} 必須為大於 0 的有限數值")
    for name, value in (("unsprung_mass", unsprung_mass), ("cog_height", cog_height)):
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"{name} 必須為大於或等於 0 的有限數值")
    front_ratio, rear_ratio = calculate_weight_distribution(front_distance, rear_distance)
    total_mass = mass + 4 * unsprung_mass
    weight = total_mass * g
    acceleration = acceleration_g * g
    transfer = total_mass * acceleration * cog_height / (front_distance + rear_distance)
    front_load = weight * front_ratio - transfer
    rear_load = weight * rear_ratio + transfer
    if front_load <= 0 or rear_load <= 0:
        raise ValueError("此 a_acc 會造成前／後軸法向載重歸零或為負，無法使用接地加速齒比模型")
    total_force = total_mass * acceleration
    front_force = total_force * front_load / weight
    rear_force = total_force * rear_load / weight
    maximum_wheel_force = max(front_force, rear_force) / 2
    wheel_torque = maximum_wheel_force * tire_radius
    ratio_accel = wheel_torque / motor_torque
    wheel_rpm = (target_speed_kmh / 3.6) / (2 * math.pi * tire_radius) * 60
    ratio_top_speed = motor_rpm / wheel_rpm
    return {
        "total_mass_kg": total_mass,
        "gear_rate_acceleration_g": acceleration_g,
        "gear_rate_target_speed_kmh": target_speed_kmh,
        "front_axle_load_N": front_load,
        "rear_axle_load_N": rear_load,
        "longitudinal_transfer_N": transfer,
        "total_Fx_N": total_force,
        "front_axle_Fx_N": front_force,
        "rear_axle_Fx_N": rear_force,
        "maximum_wheel_Fx_N": maximum_wheel_force,
        "wheel_torque_required_Nm": wheel_torque,
        "target_wheel_rpm": wheel_rpm,
        "gear_ratio_accel": ratio_accel,
        "gear_ratio_top_speed": ratio_top_speed,
        "gear_ratio_avg": (ratio_accel + ratio_top_speed) / 2,
    }


def calculate_brake_ratio(mass, unsprung_mass, cog_height, front_distance, rear_distance,
                          deceleration_g, tire_friction):
    """無空力煞車：指定減速度理想分配、可達上限分配及 Brake_ratio 十點擬合。"""
    for name, value in (("mass", mass), ("deceleration_g", deceleration_g),
                        ("tire_friction", tire_friction)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} 必須為大於 0 的有限數值")
    for name, value in (("unsprung_mass", unsprung_mass), ("cog_height", cog_height)):
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"{name} 必須為大於或等於 0 的有限數值")
    front_ratio, rear_ratio = calculate_weight_distribution(front_distance, rear_distance)
    total_mass = mass + 4 * unsprung_mass
    weight = total_mass * g
    wheelbase = front_distance + rear_distance
    lift_limit = front_distance / cog_height if cog_height > 0 else math.inf

    def point(z):
        transfer = weight * z * cog_height / wheelbase
        front_load = weight * front_ratio + transfer
        rear_load = weight * rear_ratio - transfer
        if math.isclose(rear_load, 0.0, rel_tol=0.0, abs_tol=weight * 1e-12):
            front_load, rear_load = weight, 0.0
        return {
            "deceleration_g": z,
            "front_axle_load_N": front_load,
            "rear_axle_load_N": rear_load,
            "longitudinal_transfer_N": transfer,
            "front_brake_force_N": z * front_load,
            "rear_brake_force_N": z * rear_load,
            "front_ratio": front_load / weight,
            "rear_ratio": rear_load / weight,
        }

    requested = point(deceleration_g)
    if requested['rear_axle_load_N'] < 0:
        raise ValueError("此 brake_ax 會造成後軸離地，無法使用兩軸接地的理想煞車分配模型")
    achievable_limit = min(tire_friction, lift_limit)
    design_limit = min(deceleration_g, achievable_limit)
    limit_point = point(design_limit)
    start = min(0.1, design_limit / 10)
    samples = [point(start + index * (design_limit - start) / 9) for index in range(10)]
    slope = sum(item['front_brake_force_N'] * item['rear_brake_force_N'] for item in samples) / sum(
        item['front_brake_force_N']**2 for item in samples
    )
    fitted_front_ratio = 1 / (1 + slope)
    return {
        "total_mass_kg": total_mass,
        "requested_point": requested,
        "limit_point": limit_point,
        "samples": samples,
        "required_tire_mu": deceleration_g,
        "rear_lift_limit_g": lift_limit,
        "physical_deceleration_limit_g": achievable_limit,
        "target_achievable": deceleration_g <= achievable_limit or math.isclose(
            deceleration_g, achievable_limit, rel_tol=1e-12, abs_tol=1e-12
        ),
        "brake_design_deceleration_g": design_limit,
        "brake_ideal_front_ratio": fitted_front_ratio,
        "brake_ideal_rear_ratio": 1 - fitted_front_ratio,
        "brake_ideal_fit_rear_over_front": slope,
    }


def calculate_brake_mechanical_advantage(front_brake_force, rear_brake_force, driver_force):
    """以指定工況的前後軸總煞車力除以腳力，求整體等效力放大倍率。"""
    for name, value in (("front_brake_force", front_brake_force), ("rear_brake_force", rear_brake_force)):
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"{name} 必須為大於或等於 0 的有限數值（N）")
    if not math.isfinite(driver_force) or driver_force <= 0:
        raise ValueError("driver_force 必須為大於 0 的有限數值（N）")
    total_brake_force = front_brake_force + rear_brake_force
    if not math.isfinite(total_brake_force):
        raise ValueError("前後軸總煞車力必須為有限數值（N）")
    return {
        "brake_total_required_force_N": total_brake_force,
        "brake_driver_force_N": driver_force,
        "brake_mechanical_advantage": total_brake_force / driver_force,
    }


def calculate_cg_safety(cog_height, front_track, rear_track, safety_factor):
    """沿用 CG 的 45／60 度幾何上限，回傳高度上限、餘裕與判定。"""
    for name, value in (("front_track", front_track), ("rear_track", rear_track)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} 必須為大於 0 的有限數值（m）")
    if not math.isfinite(cog_height) or cog_height < 0:
        raise ValueError("cog_height 必須為大於或等於 0 的有限數值（m）")
    if not math.isfinite(safety_factor) or safety_factor < 1:
        raise ValueError("safety_factor 必須為至少 1 的有限數值")

    width = min(front_track, rear_track)
    result = {"cg_min_track_m": width}
    for angle in (45, 60):
        limit = width / (2 * math.tan(math.radians(angle)) * safety_factor)
        margin = limit - cog_height
        at_limit = math.isclose(cog_height, limit, rel_tol=1e-12, abs_tol=1e-12)
        safe = margin > 0 and not at_limit
        result[f'cg_height_limit_{angle}_m'] = limit
        result[f'cg_height_margin_{angle}_m'] = margin
        result[f'cg_safe_{angle}'] = safe
        result[f'cg_status_{angle}'] = (
            "臨界（無高度餘裕）" if at_limit else
            "通過幾何檢查" if safe else "超過幾何上限"
        )
    result['cg_geometric_safe'] = result['cg_safe_45'] and result['cg_safe_60']
    return result


def main(*, report_path=None, write_report=True):
    if not isinstance(use_tender, bool):
        raise ValueError("use_tender 必須為布林值 True 或 False")
    wf, wr = calculate_weight_distribution(lf, lr)
    L = lf + lr
    steering_angle_deg = calculate_required_steering_angle(L, min_turn_radius_m)
    if not math.isfinite(F_ref_ratio) or not 0 <= F_ref_ratio <= 1:
        raise ValueError("F_ref_ratio 必須介於 0 與 1 之間")
    cg_result = calculate_cg_safety(h_cog, tf, tr, cg_safety_factor)
    print("\nCG：重心高度與傾斜幾何上限檢查：")
    print(f"目前重心高度 = {h_cog * 1000:.3f} mm，"
          f"採用較小輪距 = {cg_result['cg_min_track_m'] * 1000:g} mm，安全係數 = {cg_safety_factor:g}")
    for angle in (45, 60):
        print(f"{angle} deg：重心高度上限 = {cg_result[f'cg_height_limit_{angle}_m'] * 1000:.3f} mm，"
              f"高度餘裕 = {cg_result[f'cg_height_margin_{angle}_m'] * 1000:.3f} mm，"
              f"判定：{cg_result[f'cg_status_{angle}']}")
    print("整體判定：" + ("目前重心高度通過 45／60 度幾何檢查。" if cg_result['cg_geometric_safe']
                           else "目前重心高度至少一項為臨界或超過幾何上限。"))
    print("模型假設：左右對稱、無懸吊變形。")

    skidpad_result = calculate_skidpad_downforce(ms, mu, wl_mu_y, target_lap_time_s)
    print("\nskidpad_test：達到目標圈速所需的空力下壓力：")
    print(f"目標圈速 = {target_lap_time_s:g} s，整車總質量 = {skidpad_result['skidpad_total_mass_kg']:g} kg")
    print(f"Skidpad 直徑 = {skidpad_result['skidpad_diameter_m']:g} m，"
          f"係數 = {skidpad_result['skidpad_safety_factor']:g}，輪胎橫向摩擦係數 = {wl_mu_y:.6f}")
    print(f"目標車速 = {skidpad_result['skidpad_target_speed_m_per_s']:.3f} m/s "
          f"= {skidpad_result['v_ref']:.3f} km/h")
    print(f"側向加速度 = {skidpad_result['skidpad_target_lateral_acceleration_m_per_s2']:.3f} m/s^2 "
          f"= {skidpad_result['skidpad_target_lateral_acceleration_m_per_s2'] / g:.3f} g")
    print(f"含係數後的需求摩擦係數 = {skidpad_result['skidpad_target_required_mu']:.6f}")
    if skidpad_result['F_ref'] < 0:
        print(f"原公式下壓力 = {skidpad_result['F_ref']:.3f} N，輪胎摩擦力已足以達到此模型的目標。")
    print(f"在 {skidpad_result['v_ref']:.3f} km/h 所需的整車額外下壓力 "
          f"= {skidpad_result['skidpad_required_aero_downforce_N']:,.3f} N "
          f"= {skidpad_result['skidpad_required_aero_downforce_N'] / g:.3f} kgf")

    aero_result = calculate_aero_lift_coefficient(
        skidpad_result['skidpad_required_aero_downforce_N'],
        skidpad_result['skidpad_target_speed_m_per_s'], A_air, air_density_kg_per_m3
    )
    print("\n空力目標升力係數（以下壓力為正）：")
    print(f"空力有效面積 A = {A_air:g} m^2，空氣密度 rho = {air_density_kg_per_m3:g} kg/m^3，"
          f"目標車速 v = {skidpad_result['skidpad_target_speed_m_per_s']:.6f} m/s")
    print(f"依指定 F = C * rho * A * v^2：目標 C = {aero_result['target_coefficient_C']:.6f}（無因次）")
    print(f"對照原 Aero_Cl_Cd 的 F = 0.5 * Cl * rho * A * v^2："
          f"Cl = 2 * C = {aero_result['standard_downforce_coefficient_Cl']:.6f}（下壓力為正）")

    heave_result = None
    tender_result = None
    compression_result = None
    pitch_k, pitch_s = calculate_stiffness(ms, abs(ax), h_cog, L, target_pitch_angle_deg)
    roll_k, roll_s = calculate_stiffness(ms, abs(ay), h_cog, t, target_roll_angle_deg)
    travel_pitch_k, travel_pitch_angle = calculate_compressed_travel(ms, abs(ax), h_cog, L, sus_travel)
    travel_roll_k, travel_roll_angle = calculate_compressed_travel(ms, abs(ay), h_cog, t, sus_travel)

    print("\n目標角度結果：")
    print(f"Pitch @ {target_pitch_angle_deg:g} deg: {pitch_k:,.2f} N/m "
          f"= {pitch_k / 1000:.3f} N/mm, 位移 = {pitch_s * 1000:.3f} mm")
    print(f"Roll  @ {target_roll_angle_deg:g} deg: {roll_k:,.2f} N/m "
          f"= {roll_k / 1000:.3f} N/mm, 位移 = {roll_s * 1000:.3f} mm")

    print(f"\nCompressed travel @ {sus_travel * 1000:g} mm：")
    print(f"Pitch: {travel_pitch_k:,.2f} N/m = {travel_pitch_k / 1000:.3f} N/mm, "
          f"角度 = {travel_pitch_angle:.3f} deg")
    print(f"Roll : {travel_roll_k:,.2f} N/m = {travel_roll_k / 1000:.3f} N/mm, "
          f"角度 = {travel_roll_angle:.3f} deg")

    selected_pitch_k = max(pitch_k, travel_pitch_k)
    selected_roll_k = max(roll_k, travel_roll_k)
    pitch_frequency = calculate_natural_frequency(ms, selected_pitch_k)
    roll_frequency = calculate_natural_frequency(ms, selected_roll_k)

    print("\nFrequency vs stiffness（取傾斜角與壓縮行程分析較高的剛性）：")
    print(f"等效計算質量 = ms / 2 = {ms / 2:g} kg")
    print(f"Pitch K = max({pitch_k:,.2f}, {travel_pitch_k:,.2f}) "
          f"= {selected_pitch_k:,.2f} N/m, 自然頻率 = {pitch_frequency:.3f} Hz")
    print(f"Roll  K = max({roll_k:,.2f}, {travel_roll_k:,.2f}) "
          f"= {selected_roll_k:,.2f} N/m, 自然頻率 = {roll_frequency:.3f} Hz")

    tire_result = calculate_tire_stiffness(MR, Kt, selected_pitch_k, selected_roll_k)
    print("\nTire stiffness（計入輪胎柔度後的彈簧剛性）：")
    print(f"MR = {MR:g}, 單輪 Kt = {Kt:,.2f} N/m")
    print(f"目標 ride rate = (K_roll + K_pitch) / 4 "
          f"= {tire_result['target_ride_rate_N_per_m']:,.2f} N/m")
    print(f"一般 Ks（20,000～80,000 N/m 取樣搜尋）= {tire_result['Ks']:,.2f} N/m "
          f"= {tire_result['Ks'] / 1000:.3f} N/mm")
    print(f"選定 Ks 對應的 ride rate = {tire_result['actual_ride_rate_N_per_m']:,.2f} N/m")
    print(f"Pitch Ks = {tire_result['Ks_pitch_N_per_m']:,.2f} N/m "
          f"= {tire_result['Ks_pitch_N_per_m'] / 1000:.3f} N/mm")
    print(f"Roll  Ks = {tire_result['Ks_roll_N_per_m']:,.2f} N/m "
          f"= {tire_result['Ks_roll_N_per_m'] / 1000:.3f} N/mm")

    mass_result = calculate_frequency_vs_mass(
        ms, mu, MR, Kt, tire_result['Ks_pitch_N_per_m'], tire_result['Ks_roll_N_per_m']
    )
    print("\nFrequency vs mass（簧上／簧下自然頻率估算）：")
    print(f"整車總質量 = ms + 4 * mu = {mass_result['m_total_vehicle_kg']:g} kg")
    print(f"四分之一車簧上質量 = ms / 4 = {mass_result['quarter_sprung_mass_kg']:g} kg")
    print(f"單輪簧下質量 mu = {mu:g} kg, "
          f"簧下質量比例 = {mass_result['unsprung_mass_ratio_target_percent']:.3f}%")
    print(f"等效彈簧剛性 = (Ks_roll + Ks_pitch) / 4 "
          f"= {mass_result['equivalent_spring_stiffness_N_per_m']:,.2f} N/m")
    print(f"輪率 Kw = {mass_result['wheel_rate_N_per_m']:,.2f} N/m, "
          f"ride rate Kr = {mass_result['ride_rate_N_per_m']:,.2f} N/m")
    print(f"簧上自然頻率 = {mass_result['frequency_sprung_target_Hz']:.3f} Hz")
    print(f"簧下自然頻率（Wheel-hop）= {mass_result['frequency_unsprung_target_Hz']:.3f} Hz")

    if not use_tender:
        print("\nTender 已關閉（use_tender = False）：跳過 Heave 反算與 Tender 可行性計算。")
        print(f"直接使用原 Heave 主簧剛性 = {tire_result['Ks_pitch_N_per_m']:,.2f} N/m")
    else:
        heave_result = calculate_heave_reduction(
            ms, mu, MR, Kt, tire_result['Ks_pitch_N_per_m'], tire_result['Ks_roll_N_per_m'],
            N
        )
        print("\nHeave 剛性反算（與 Frequency vs mass 相同的計算模式）：")
        print(f"目標簧上自然頻率 = 目前簧下頻率 / N "
              f"= {heave_result['current_unsprung_frequency_Hz']:.3f} / {N:g} "
              f"= {heave_result['target_natural_frequency_Hz']:.3f} Hz")
        print(f"固定 Roll Ks = {tire_result['Ks_roll_N_per_m']:,.2f} N/m")
        print(f"目前簧上自然頻率 = {heave_result['current_sprung_frequency_Hz']:.3f} Hz")
        if not heave_result['can_reach_target']:
            print(heave_result['reason'])
        else:
            print(f"Heave Ks：{tire_result['Ks_pitch_N_per_m']:,.2f} "
                  f"→ {heave_result['Ks_required_target_frequency_N_per_m']:,.2f} N/m")
            reduction = heave_result['heave_stiffness_reduction_N_per_m']
            if reduction >= 0:
                print(f"需降低 {reduction:,.2f} N/m "
                      f"（{heave_result['heave_stiffness_reduction_percent']:.3f}%）")
            else:
                print(f"需增加 {-reduction:,.2f} N/m "
                      f"（{-heave_result['heave_stiffness_reduction_percent']:.3f}%）")
            print(f"新 heave 剛性 = 原剛性的 {heave_result['Ks_scale_target_frequency']:.6f} 倍")
            print(f"調整後回算：簧上自然頻率 = {heave_result['adjusted_sprung_frequency_Hz']:.3f} Hz，"
                  f"簧下自然頻率 = {heave_result['adjusted_unsprung_frequency_Hz']:.3f} Hz")

            print("\n2_spring（主 heave 彈簧與 Tender 串聯）：")
            if not 0 < heave_result['Ks_scale_target_frequency'] < 1:
                print("目標 heave 剛性未低於主簧剛性，無法以有限正剛性的串聯 tender 達成。")
            else:
                tender_result = calculate_tender_stiffness(
                    tire_result['Ks_pitch_N_per_m'], heave_result['Ks_scale_target_frequency']
                )
                print(f"主 heave 彈簧 K_main = {tender_result['K_heave_main_N_per_m']:,.2f} N/m")
                print(f"目標串聯剛性 K_series = {tender_result['K_series_target_N_per_m']:,.2f} N/m")
                print(f"所需 Tender 剛性 = {tender_result['K_tender_required_N_per_m']:,.2f} N/m "
                      f"= {tender_result['K_tender_required_N_per_m'] / 1000:.3f} N/mm")
                print(f"Tender / 主簧剛性比 = {tender_result['tender_to_heave_stiffness_ratio']:.6f} 倍")

    series_heave = tender_result['K_heave_with_tender_N_per_m'] if tender_result is not None else None
    active_heave = series_heave if use_tender else tire_result['Ks_pitch_N_per_m']

    anti_dive_result = calculate_anti_dive(rc_chassis_stiffness_ratio)
    print("\nAnti dive（與前 Roll Center 相同的正規化兩路模型）：")
    print(f"車體／懸吊剛性比 c = {rc_chassis_stiffness_ratio:g}，K_eq / Ks = (1 - a)^2 + c * a^2")
    print(f"懸吊路徑比例 alpha = c / (1 + c) = {anti_dive_result['anti_dive_suspension_fraction']:.6f}")
    print(f"anti_dive = 1 / (1 + c) = {anti_dive_result['anti_dive']:.6f} "
          f"= {anti_dive_result['anti_dive_percent']:.3f}%")
    print(f"最小正規化等效剛性 K_eq / Ks = {anti_dive_result['anti_dive_normalized_min_stiffness']:.6f}")

    print("\nAnti-Scrub（依指定公式）：")
    anti_scrub_result = calculate_anti_scrub(anti_dive_result['anti_dive'], a_acc, ax)
    print(f"ax = {ax:g} g，a_acc = {a_acc:g} g")
    print(f"anti_scrub = anti_dive * a_acc / ax "
          f"= {anti_dive_result['anti_dive']:.6f} * {a_acc:g} / {ax:g} "
          f"= {anti_scrub_result['anti_scrub']:.6f} "
          f"= {anti_scrub_result['anti_scrub_percent']:.3f}%")

    rc_result = calculate_roll_center(h_cog, rc_chassis_stiffness_ratio)
    print("\nroll_center：正規化等效剛性與 Roll Center 高度：")
    print(f"車架／懸吊剛性比 c = {rc_chassis_stiffness_ratio:g}, 重心高度 = {h_cog:g} m")
    print(f"懸吊路徑比例 alpha = c / (1 + c) = {rc_result['rc_suspension_fraction']:.6f}")
    print(f"最小正規化等效剛性 K_eq / Ks = {rc_result['rc_normalized_min_stiffness']:.6f}（無因次）")
    print(f"對應 RC / CG = {rc_result['rc_normalized_optimal_ratio']:.6f} "
          f"（重心高度的 {rc_result['rc_normalized_optimal_ratio'] * 100:.3f}%）")
    print(f"前輪 Roll Center 高度（解析解）= {rc_result['rc_normalized_optimal_height_m']:.6f} m "
          f"= {rc_result['rc_normalized_optimal_height_m'] * 1000:.3f} mm")

    rear_rc_height = calculate_rear_roll_center(
        rc_result['rc_normalized_optimal_height_m'], wf, wr, tf, tr, kf, kr
    )
    print("\n後輪 Roll Center 高度計算：")
    print(f"重心到前軸 lf = {lf:g} m，重心到後軸 lr = {lr:g} m，軸距 L = {L:g} m")
    print(f"前軸重量比例 wf = lr / L = {wf:.3%}，後軸重量比例 wr = lf / L = {wr:.3%}")
    print(f"前後重量比 wf:wr = {wf:.3%}:{wr:.3%}，前後剛性比 kf:kr = {kf:.0%}:{kr:.0%}")
    print(f"前輪距 tf = {tf * 1000:g} mm，後輪距 tr = {tr * 1000:g} mm")
    print(f"後 RC = 前 RC × (wf/wr) × (tr/tf) × (kf/kr) "
          f"= 前 RC × {wf / wr:.6f} × {tr / tf:.6f} × {kf / kr:.6f}")
    print(f"後輪 Roll Center 高度 = {rear_rc_height:.6f} m = {rear_rc_height * 1000:.3f} mm")

    print("\nFVSA：最大 Roll 角、虛擬擺臂長度與 Camber gain（依指定公式）：")
    print(f"行程 d = sus_travel = {sus_travel:g} m（{sus_travel * 1000:g} mm）；公式固定以公尺代入。")
    fvsa_results = {}
    for axle_name, track in (("前軸", tf), ("後軸", tr)):
        fvsa_result = calculate_fvsa(sus_travel, track)
        fvsa_results[axle_name] = fvsa_result
        print(f"{axle_name}輪距 = {track * 1000:g} mm，最大 Roll 角 theta = {fvsa_result['max_roll_angle_deg']:.6f} deg")
        print(f"  FVSA = 1 / tan(theta / (2*d)) = {fvsa_result['fvsa_length_m']:.6f} m "
              f"= {fvsa_result['fvsa_length_mm']:.3f} mm")
        print(f"  Camber gain（按 1 m 位移後比例換算）= {fvsa_result['camber_gain_deg_per_m']:.6f} deg/m "
              f"= {fvsa_result['camber_gain_deg_per_mm']:.6f} deg/mm")
        print(f"  最大 Camber 變化角 = camber_gain * d = {fvsa_result['max_camber_change_deg']:.6f} deg")

    print("\n純 ay：輪胎壓縮差造成的額外 Roll（ax = 0、空力下壓力 = 0）：")
    print(f"側向加速度 = {ay:g} g = {ay * g:.3f} m/s^2；"
          f"各軸質量依 wf:wr = {wf:.3%}:{wr:.3%} 分配。")
    print("各軸視為左右兩輪模型，僅計輪胎垂直剛性 Kt，不加入懸吊彈簧剛性。")
    total_mass = ms + 4 * mu
    tire_roll_results = {}
    for axle_name, mass_fraction, track in (("前軸", wf, tf), ("後軸", wr, tr)):
        tire_roll = calculate_lateral_tire_roll(total_mass * mass_fraction, h_cog, track, Kt, ay)
        tire_roll_results[axle_name] = tire_roll
        print(f"{axle_name}質量 = {tire_roll['axle_mass_kg']:.3f} kg，"
              f"Fy = m * ay = {tire_roll['lateral_force_N']:.3f} N，"
              f"側傾力矩 Fy * h = {tire_roll['roll_moment_Nm']:.3f} Nm")
        print(f"  左輪 Fz = {tire_roll['left_normal_load_N']:.3f} N，"
              f"右輪 Fz = {tire_roll['right_normal_load_N']:.3f} N，"
              f"右減左輪載差 = {tire_roll['normal_load_difference_N']:.3f} N")
        print(f"  靜態單輪壓縮 = {tire_roll['static_compression_m'] * 1000:.3f} mm；"
              f"線性總壓縮 Fz/Kt：左 = {tire_roll['left_linear_compression_m'] * 1000:.3f} mm，"
              f"右 = {tire_roll['right_linear_compression_m'] * 1000:.3f} mm")
        print(f"  ay 造成的壓縮增減量：左 = {tire_roll['left_compression_change_m'] * 1000:.3f} mm，"
              f"右 = {tire_roll['right_compression_change_m'] * 1000:.3f} mm；"
              f"右減左壓縮差 = {tire_roll['deformation_difference_m'] * 1000:.3f} mm")
        if tire_roll['contact_valid']:
            state = "離地臨界" if tire_roll['at_lift_boundary'] else "兩輪接地"
            print(f"  {state}：額外輪胎 Roll = 壓縮差 / 輪距 "
                  f"= {tire_roll['tire_roll_angle_rad']:.6f} rad "
                  f"= {tire_roll['tire_roll_angle_deg']:.6f} deg（小角度）")
        else:
            print(f"  內側輪載為負，超過離地界限 {tire_roll['ay_contact_limit_g']:.6f} g；"
                  "此兩輪接地模型無有效解。")
            print(f"  線性外推 Roll 參考值 = {tire_roll['linear_tire_roll_angle_deg']:.6f} deg；"
                  "負壓縮量不代表輪胎可承受拉力。")

    front_fvsa = fvsa_results["前軸"]
    front_tire_roll = tire_roll_results["前軸"]
    caster_result = calculate_caster_for_zero_camber(
        front_fvsa['max_roll_angle_deg'], front_tire_roll['linear_tire_roll_angle_deg'],
        front_fvsa['max_camber_change_deg'], kpi_deg, steering_angle_deg
    )
    print("\nCaster：疊加前軸 Roll、輪胎傾斜與 FVSA 後，反解前輪 Camber = 0：")
    print(f"最小轉彎半徑 R = {min_turn_radius_m:g} m，軸距 L = {L:g} m；"
          f"最大需求轉向角 theta = atan(L/R) = {steering_angle_deg:.6f} deg（單軌等效前輪角）")
    print(f"初始 Camber = 0 deg；採 sus_travel 對應的前軸最大 Roll；"
          f"KPI = {kpi_deg:g} deg，固定正方向 delta = {steering_angle_deg:+.6f} deg。")
    print("delta 為公式中的前輪轉向角；方向盤角度需先依轉向比換算。公式內所有角度以 rad 計算。")
    print(f"方向驗證：固定較大的 Caster = {caster_direction_check_deg:g} deg；以下比較僅供查核，不修改設定。")
    steering_checks = []
    for check_angle in (abs(steering_angle_deg), -abs(steering_angle_deg)):
        check_change = calculate_steering_camber(caster_direction_check_deg, kpi_deg, check_angle)
        steering_checks.append({"steering_angle_deg": check_angle, "raw_camber_change_deg": check_change})
        print(f"  驗證 delta = {check_angle:+.6f} deg：原式 Delta camber = {check_change:+.6f} deg，"
              f"絕對值 = {abs(check_change):.6f} deg")
    print(f"轉向前 Camber = Roll + 輪胎 Roll - FVSA Camber 變化 "
          f"= {front_fvsa['max_roll_angle_deg']:.6f} + {front_tire_roll['linear_tire_roll_angle_deg']:.6f} "
          f"- {front_fvsa['max_camber_change_deg']:.6f} = {caster_result['base_camber_deg']:.6f} deg")
    if not front_tire_roll['contact_valid']:
        print("前軸純 ay 接地模型失效；以下 Caster 與 Camber 僅為線性外推參考值。")
    if caster_result['solution_status'] == 'solved':
        label = "線性外推參考 Caster" if not front_tire_roll['contact_valid'] else "所需 Caster"
        print(f"sin(caster) = {caster_result['required_caster_sine']:.9f}；"
              f"{label} = {caster_result['caster_deg']:.6f} deg（-90～90 deg 主值）")
        print(f"固定方向原式分項：Caster = {caster_result['caster_camber_change_deg']:+.6f} deg；"
              f"KPI = {caster_result['kpi_camber_change_deg']:+.6f} deg")
        print(f"固定 delta = {steering_angle_deg:+.6f} deg 的原式 Delta camber "
              f"= {caster_result['raw_steering_camber_change_deg']:+.6f} deg")
        print(f"固定座標換算：套用量 = -原式值 "
              f"= {caster_result['steering_camber_change_deg']:.6f} deg；"
              f"回代前輪 Camber = {caster_result['final_camber_deg']:.9f} deg")
    elif caster_result['solution_status'] == 'underdetermined':
        print("delta = 0 且原 Camber 已為 0；此公式無法決定唯一 Caster。")
    else:
        print("指定方向規則下無可行 Caster：" + caster_result['reason'])

    print("\nTender：所需下壓力造成的壓縮變形量（無煞車、下壓力前後均分）：")
    if not use_tender:
        print("Tender 已關閉，略過 Tender 串聯壓縮計算。")
    elif tender_result is None:
        print("前序 2_spring 沒有可行的 Tender 剛性，無法計算串聯壓縮量。")
    else:
        compression_result = calculate_tender_compression(
            tender_result['K_heave_main_N_per_m'], tender_result['tender_to_heave_stiffness_ratio'],
            skidpad_result['skidpad_required_aero_downforce_N'], F_ref_ratio
        )
        print(f"施加下壓力比例 = {F_ref_ratio:.0%}，整車下壓力 "
              f"= {compression_result['tender_bind_vehicle_downforce_N']:.3f} N")
        print(f"前後各一組彈簧，單組承受力 = {compression_result['tender_bind_force_N']:.3f} N")
        print(f"單組主簧壓縮量 = {compression_result['main_spring_compression_mm']:.3f} mm")
        print(f"單組 Tender 壓縮量 = {compression_result['tender_bind_spring_stroke_mm']:.3f} mm")
        print(f"單組總壓縮量 = 主簧 + Tender = {compression_result['tender_bind_total_stroke_mm']:.3f} mm")
        print(f"前懸吊壓縮量 = {compression_result['front_compression_mm']:.3f} mm，"
              f"後懸吊壓縮量 = {compression_result['rear_compression_mm']:.3f} mm，"
              f"Heave = {compression_result['heave_mm']:.3f} mm")
        print("以上為相對原平衡位置的增量；依原 Tender 設定，此工況為 Tender 壓實設計切換點。")

    applied_downforce = skidpad_result['skidpad_required_aero_downforce_N'] * F_ref_ratio
    front_roll_stiffness = tire_result['Ks_roll_N_per_m'] * (MR * tf)**2
    rear_roll_stiffness = tire_result['Ks_roll_N_per_m'] * (kr / kf) * (MR * tr)**2
    wheel_load_result = calculate_suspension_wheel_loads(
        ms, mu, h_cog, lf, lr, tf, tr, ax, ay, applied_downforce,
        wl_aero_front_ratio, front_roll_stiffness, rear_roll_stiffness
    )
    force_result = calculate_tire_force_demands(
        wheel_load_result['wheel_loads_N'], wheel_load_result['total_mass_kg'], ax, ay
    )
    print("\nsus_load：空力與 x／y 加速度下的四輪受力：")
    print("座標：x 向前、y 向左、z 向上；正 ax 後軸增載，正 ay 右輪增載。")
    print(f"整車質量 = {wheel_load_result['total_mass_kg']:g} kg，ax = {ax:g} g，ay = {ay:g} g")
    print(f"施加空力下壓力 = {applied_downforce:.3f} N，"
          f"空力前後分配 = {wl_aero_front_ratio:.1%}:{1 - wl_aero_front_ratio:.1%}")
    print(f"前後 Roll 剛性 = {front_roll_stiffness:,.3f}／{rear_roll_stiffness:,.3f} Nm/rad，"
          f"前軸滾轉力矩比例 = {wheel_load_result['front_roll_fraction']:.3%}")
    print(f"縱向載重轉移 = {wheel_load_result['longitudinal_transfer_N']:,.3f} N，"
          f"前軸總輪載 = {wheel_load_result['front_axle_load_N']:,.3f} N，"
          f"後軸總輪載 = {wheel_load_result['rear_axle_load_N']:,.3f} N")
    print(f"整車需求 Fx = m * ax * g = {force_result['total_Fx_N']:,.3f} N，"
          f"Fy = m * ay * g = {force_result['total_Fy_N']:,.3f} N")
    print("Fx、Fy 按非負輪載占比分配；屬同一工況的需求力估算，未指定驅動、煞車或轉向分配。")
    if force_result['reference_only']:
        unloaded = ", ".join(wheel for wheel, load in wheel_load_result['wheel_loads_N'].items() if load < 0)
        print(f"接地假設失效：{unloaded} 原始輪載為負；未重解離地工況，以下三向力及最大合力僅供參考。")
        print(f"原始四輪 Fz 總和 = {wheel_load_result['total_normal_load_N']:,.3f} N，"
              f"截零後總和 = {force_result['clipped_total_Fz_N']:,.3f} N；截零結果不滿足垂向力平衡。")
    else:
        print("接地檢查：四輪原始輪載皆非負。")
    print(f"{'輪胎':<6}{'原始 Fz [N]':>16}{'Fx [N]':>14}{'Fy [N]':>14}{'Fz [N]':>14}{'合力 [N]':>14}")
    for wheel, values in force_result['wheel_forces'].items():
        print(f"{wheel:<6}{values['raw_Fz_N']:>16,.3f}{values['Fx_N']:>14,.3f}"
              f"{values['Fy_N']:>14,.3f}{values['Fz_N']:>14,.3f}{values['force_magnitude_N']:>14,.3f}")
    wheel_names = {"FL": "左前輪", "FR": "右前輪", "RL": "左後輪", "RR": "右後輪"}
    maximum_wheel = force_result['most_loaded_wheel']
    maximum = force_result['wheel_forces'][maximum_wheel]
    label = "最大參考合力輪胎" if force_result['reference_only'] else "合力最大的輪胎"
    print(f"{label}：{maximum_wheel}（{wheel_names[maximum_wheel]}）")
    print(f"|Fx| = {abs(maximum['Fx_N']):,.3f} N，|Fy| = {abs(maximum['Fy_N']):,.3f} N，"
          f"Fz = {maximum['Fz_N']:,.3f} N，合力 = {maximum['force_magnitude_N']:,.3f} N")

    gear_result = calculate_gear_rate(
        ms, mu, h_cog, lf, lr, a_acc, R_tire, drive_motor_torque_Nm,
        drive_motor_rpm, drive_target_speed_kmh
    )
    print("\nGear_rate：無空力加速與極速齒比：")
    print(f"工況：ax = a_acc = {a_acc:g} g，ay = 0 g，空力下壓力 = 0 N")
    print(f"整車質量 = {gear_result['total_mass_kg']:g} kg，輪胎半徑 = {R_tire:g} m")
    print(f"前軸輪載 = {gear_result['front_axle_load_N']:,.3f} N，"
          f"後軸輪載 = {gear_result['rear_axle_load_N']:,.3f} N，"
          f"縱向載重轉移 = {gear_result['longitudinal_transfer_N']:,.3f} N")
    print(f"整車加速需求力 = {gear_result['total_Fx_N']:,.3f} N，"
          f"前軸需求 = {gear_result['front_axle_Fx_N']:,.3f} N，"
          f"後軸需求 = {gear_result['rear_axle_Fx_N']:,.3f} N")
    print(f"最大單輪需求力 = {gear_result['maximum_wheel_Fx_N']:,.3f} N，"
          f"單輪需求扭矩 = {gear_result['wheel_torque_required_Nm']:,.3f} Nm")
    print(f"單顆馬達最大扭矩 = {drive_motor_torque_Nm:g} Nm，最高轉速 = {drive_motor_rpm:g} rpm")
    print(f"目標極速 = {drive_target_speed_kmh:g} km/h，輪速 = {gear_result['target_wheel_rpm']:,.3f} rpm")
    print(f"加速減速比 gear_ratio_accel = {gear_result['gear_ratio_accel']:.6f}:1")
    print(f"極速減速比 gear_ratio_top_speed = {gear_result['gear_ratio_top_speed']:.6f}:1")
    print(f"平均減速比 gear_ratio_avg = (加速減速比 + 極速減速比) / 2 "
          f"= {gear_result['gear_ratio_avg']:.6f}:1")
    print("模型假設：依輪載比例分配加速需求、每軸兩輪均分且每輪一顆馬達；未計傳動效率及行駛阻力。")

    brake_result = calculate_brake_ratio(ms, mu, h_cog, lf, lr, brake_ax, mu_w)
    requested_brake = brake_result['requested_point']
    limit_brake = brake_result['limit_point']
    print("\nBrake_ratio：極限煞車工況的前後煞車比：")
    print(f"指定工況：減速度 brake_ax = {brake_ax:g} g（車身 ax = {-brake_ax:g} g），"
          "ay = 0 g，空力下壓力 = 0 N")
    print(f"前軸輪載 = {requested_brake['front_axle_load_N']:,.3f} N，"
          f"後軸輪載 = {requested_brake['rear_axle_load_N']:,.3f} N，"
          f"煞車載重轉移 = {requested_brake['longitudinal_transfer_N']:,.3f} N")
    print(f"指定工況前軸煞車力需求 = {requested_brake['front_brake_force_N']:,.3f} N，"
          f"後軸煞車力需求 = {requested_brake['rear_brake_force_N']:,.3f} N")
    print(f"{brake_ax:g} g 理想前後煞車比 = "
          f"{requested_brake['front_ratio']:.3%}:{requested_brake['rear_ratio']:.3%}")
    print(f"縱向摩擦係數 mu_w = {mu_w:.6f}，指定工況所需 mu_x = {brake_result['required_tire_mu']:g}，"
          f"後軸離地界限 = {brake_result['rear_lift_limit_g']:.3f} g")
    if not brake_result['target_achievable']:
        print(f"指定 {brake_ax:g} g 超出無空力可達上限；上列為理想設計需求。"
              f"目前可達上限 = {brake_result['physical_deceleration_limit_g']:.6f} g。")
    else:
        print("指定減速度通過輪胎摩擦與後軸接地檢查。")
    print(f"本次可達極限工況 {limit_brake['deceleration_g']:.6f} g 的前後煞車比 = "
          f"{limit_brake['front_ratio']:.3%}:{limit_brake['rear_ratio']:.3%}")
    print(f"Brake_ratio 十點回歸範圍 = {brake_result['samples'][0]['deceleration_g']:g}～"
          f"{brake_result['brake_design_deceleration_g']:.6f} g，"
          f"擬合固定前後比 = {brake_result['brake_ideal_front_ratio']:.3%}:"
          f"{brake_result['brake_ideal_rear_ratio']:.3%}")
    print("以上為輪胎接地煞車力比例；踏板 balance bar 推力與油壓分配需另依煞車硬體換算。")

    mechanical_advantage_result = calculate_brake_mechanical_advantage(
        requested_brake['front_brake_force_N'], requested_brake['rear_brake_force_N'],
        brake_driver_force_N
    )
    print("\n煞車機構整體等效機械利益：")
    print(f"採用指定 {brake_ax:g} g 工況的最大總煞車力需求，車手腳力 "
          f"= {mechanical_advantage_result['brake_driver_force_N']:g} N")
    print(f"最大總煞車力 = 前軸 + 後軸 = {requested_brake['front_brake_force_N']:,.3f} "
          f"+ {requested_brake['rear_brake_force_N']:,.3f} "
          f"= {mechanical_advantage_result['brake_total_required_force_N']:,.3f} N")
    print(f"煞車機構機械利益 = 最大總煞車力 / 車手腳力 "
          f"= {mechanical_advantage_result['brake_total_required_force_N']:,.3f} / {brake_driver_force_N:g} "
          f"= {mechanical_advantage_result['brake_mechanical_advantage']:.6f} 倍")
    print("此為踏板端至四輪接地總煞車力的整體等效倍率。")

    damping_result = calculate_suspension_critical_damping(
        ms, wf, tire_result['Ks_roll_N_per_m'], tire_result['Ks_roll_N_per_m'] * kr / kf,
        tire_result['Ks_pitch_N_per_m'],
        series_heave,
        MR, tf, tr, sprung_roll_inertia_kg_m2
    )
    print("\n臨界阻尼：Roll、Heave + Tender、純 Heave 的前後阻尼器：" if use_tender
          else "\n臨界阻尼：Roll、純 Heave 的前後阻尼器：")
    print("每軸各一支 Heave 與一支 Roll 阻尼器；彈簧與阻尼器共用 MR，以下為阻尼器端係數。")
    print(f"前軸簧上質量 = ms * wf = {ms * wf:.6f} kg；"
          f"後軸簧上質量 = ms * wr = {ms * wr:.6f} kg；MR = {MR:g}")
    print(f"簧上 Ixx = {sprung_roll_inertia_kg_m2:.9f} kg m^2（手動初值取自既有 COG 結果）")
    print(f"整車 Roll 剛性 = {damping_result['roll_total_stiffness_Nm_per_rad']:.6f} Nm/rad；"
          f"整車臨界角阻尼 = {damping_result['roll_total_critical_damping_Nms_per_rad']:.6f} Nm s/rad")
    print("Roll 的前後值按各軸角剛性比例分配同一整車模態的臨界角阻尼，再除以 (MR * track)^2。")
    if use_tender:
        print("Heave + Tender 為串聯未併圈；純 Heave 為原主簧（Tender 併圈後），前後採相同彈簧剛性。")
    else:
        print("Tender 已關閉，Heave 直接使用原主簧剛性，前後採相同彈簧剛性。")
    print(f"{'模式':<20}{'前阻尼器 [N s/m]':>22}{'後阻尼器 [N s/m]':>22}")
    for label, mode in (("Roll", "roll"), ("Heave + Tender", "heave_with_tender"), ("純 Heave", "pure_heave")):
        if mode == "heave_with_tender" and not use_tender:
            continue
        values = damping_result[mode]
        if values is None:
            print(f"{label}：前序 Tender 無有限正剛性解，略過此工況的臨界阻尼。")
            continue
        front_c = values['front']['damper_critical_damping_Ns_per_m']
        rear_c = values['rear']['damper_critical_damping_Ns_per_m']
        print(f"{label:<20}{front_c:>22,.6f}{rear_c:>22,.6f}")
        print(f"  換算 N s/mm：前 = {front_c / 1000:.6f}，後 = {rear_c / 1000:.6f}")
    print("以上為固定輪端、剛性車體的單自由度臨界參考（zeta = 1），未加入輪胎及簧下動態。")

    rate_cases = calculate_rate_cases(
        ms, wf, MR, Kt, tire_result['Ks_roll_N_per_m'], tire_result['Ks_roll_N_per_m'] * kr / kf,
        tire_result['Ks_pitch_N_per_m'], active_heave
    )
    print("\nKs spring rate → Kw wheel rate → Kr ride rate：四種指定 Ks 的前後比較：")
    heave_label = "K_heave&tender" if use_tender else "K_heave"
    print(f"各組 Ks 直接視為單輪等效輸入；組合值依指定採 ({heave_label} + K_roll)/2。")
    print("Kw = Ks * MR^2；Kr = Kw * Kt/(Kw + Kt)，Kt 為單輪輪胎剛性。")
    print("Ks 座標質量 = 每輪簧上質量/MR^2；Kw、Kr 使用每輪簧上質量，所以 f_Ks = f_Kw。")
    case_labels = (("combined_average", f"({heave_label} + K_roll)/2"),
                   ("heave_with_tender", heave_label), ("roll", "K_roll"), ("heave_only", "K_heaveonly"))
    for axle, axle_label, fraction in (("front", "前軸", wf), ("rear", "後軸", wr)):
        print(f"{axle_label}每輪簧上質量 = ms * 軸重量比例/2 = {ms * fraction / 2:.6f} kg")
        for mode, label in case_labels:
            values = rate_cases[axle][mode]
            if values is None:
                print(f"  {label}：Tender 無可行解，略過此組。")
                continue
            print(f"  {label}：Ks = {values['spring_rate_N_per_m']:.6f} → "
                  f"Kw = {values['wheel_rate_N_per_m']:.6f} → Kr = {values['ride_rate_N_per_m']:.6f} N/m")
            print(f"    自然頻率：Ks 端 = {values['frequency_Ks_Hz']:.6f}，"
                  f"Kw 端 = {values['frequency_Kw_Hz']:.6f}，Kr 等效 = {values['frequency_Kr_Hz']:.6f} Hz")
            print(f"    臨界阻尼：Ks 端 = {values['critical_damping_Ks_Ns_per_m']:.6f}，"
                  f"Kw 端 = {values['critical_damping_Kw_Ns_per_m']:.6f}，"
                  f"Kr 等效 = {values['critical_damping_Kr_Ns_per_m']:.6f} N s/m")
    print("Kr 臨界阻尼是 ride 等效 SDOF 參考，不能直接當成實體阻尼器係數；本段不將簧下動態併入單一質量。")

    gradients = calculate_roll_pitch_gradients(
        ms + 4 * mu, h_cog, lf, lr, tf, tr, MR, Kt,
        tire_result['Ks_roll_N_per_m'], tire_result['Ks_roll_N_per_m'] * kr / kf,
        tire_result['Ks_pitch_N_per_m'], series_heave,
        rc_result['rc_normalized_optimal_height_m'], rear_rc_height, anti_dive_result['anti_dive']
    )
    print("\nRoll & Pitch gradient（準靜態、小角度，deg/g）：")
    print(f"慣性力使用整車質量 {ms + 4 * mu:.6f} kg；空力不加入質量。")
    print(f"CG 處 Roll axis 高度 = {gradients['roll_axis_height_at_cg_m'] * 1000:.6f} mm，"
          f"Roll 力臂 h_cog - h_roll_axis = {gradients['roll_moment_arm_m']:.6f} m")
    print(f"Roll gradient：僅懸吊 = {gradients['roll_gradient_suspension_deg_per_g']:.6f} deg/g；"
          f"含輪胎柔度 = {gradients['roll_gradient_with_tires_deg_per_g']:.6f} deg/g")
    for mode, label in (("heave_with_tender", "Heave + Tender（串聯未併圈）"), ("heave_only", "純 Heave（Tender 併圈後）")):
        if not use_tender:
            if mode == "heave_with_tender":
                continue
            label = "純 Heave（原主簧）"
        values = gradients['pitch'][mode]
        if values is None:
            print(f"Pitch gradient {label}：Tender 無可行解，略過此工況。")
            continue
        print(f"Pitch gradient {label}：僅懸吊 = {values['gradient_suspension_deg_per_g']:.6f}，"
              f"含輪胎 = {values['gradient_with_tires_deg_per_g']:.6f}，"
              f"含輪胎及 Anti dive {anti_dive_result['anti_dive']:.3%} "
              f"= {values['gradient_with_tires_and_anti_dive_deg_per_g']:.6f} deg/g")
    print("Gradient 是各固定剛性階段的局部斜率；Anti dive 欄為煞車方向，僅降低懸吊變形，輪胎變形仍保留。")

    parameter_names = (
        "use_tender", "ms", "mu", "h_cog", "lf", "lr", "ax", "ay", "a_acc", "brake_ax", "target_lap_time_s",
        "drive_target_speed_kmh", "sus_travel", "tf", "tr", "t", "A_air", "air_density_kg_per_m3",
        "kf", "kr", "target_pitch_angle_deg", "target_roll_angle_deg", "kpi_deg", "min_turn_radius_m",
        "caster_direction_check_deg", "MR", "sprung_roll_inertia_kg_m2", "Kt", "wl_mu_y", "mu_w",
        "R_tire", "drive_motor_torque_Nm", "drive_motor_rpm", "N", "rc_chassis_stiffness_ratio",
        "F_ref_ratio", "wl_aero_front_ratio", "cg_safety_factor", "brake_driver_force_N", "g",
    )
    parameters = {name: globals()[name] for name in parameter_names}
    parameters.update(L=L, wf=wf, wr=wr, steering_angle_deg=steering_angle_deg,
                      active_heave_spring_N_per_m=active_heave)
    snapshot = {
        "parameters": parameters, "cg": cg_result, "skidpad": skidpad_result, "aero": aero_result,
        "angle_stiffness": {
            "pitch": {"stiffness_N_per_m": pitch_k, "displacement_m": pitch_s},
            "roll": {"stiffness_N_per_m": roll_k, "displacement_m": roll_s},
        },
        "compressed_travel": {
            "pitch": {"stiffness_N_per_m": travel_pitch_k, "angle_deg": travel_pitch_angle},
            "roll": {"stiffness_N_per_m": travel_roll_k, "angle_deg": travel_roll_angle},
        },
        "selected_stiffness": {
            "pitch": {"stiffness_N_per_m": selected_pitch_k, "frequency_Hz": pitch_frequency},
            "roll": {"stiffness_N_per_m": selected_roll_k, "frequency_Hz": roll_frequency},
        },
        "tire": tire_result, "frequency_mass": mass_result, "heave": heave_result,
        "tender": tender_result, "anti_dive": anti_dive_result, "anti_scrub": anti_scrub_result,
        "front_rc": rc_result, "rear_rc_height_m": rear_rc_height, "fvsa": fvsa_results,
        "lateral_tire_roll": tire_roll_results, "caster": caster_result, "steering_checks": steering_checks,
        "compression": compression_result, "wheel_loads": wheel_load_result, "tire_forces": force_result,
        "gear": gear_result, "brake": brake_result, "brake_mechanical_advantage": mechanical_advantage_result,
        "damping": damping_result, "rate_cases": rate_cases, "gradients": gradients,
    }
    if write_report:
        destination = write_markdown_report(snapshot, report_path if report_path is not None else DEFAULT_REPORT_PATH)
        print(f"\nMarkdown 計算報告已更新：{destination}")
    return snapshot

if __name__ == "__main__":
    main()
