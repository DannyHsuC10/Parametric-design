import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")


# =========================================================
# 齒數組合計算
# =========================================================

# Parameters
M = param.M_gear          # 製作模數 [mm]
z = param.z_gear         # 目標齒比
D_max = param.D_max      # 齒輪箱直徑

T_min = 20       # 最小齒數

# =========================================================
# 總齒數限制
# =========================================================

T_all = math.floor(D_max / M)

print(f"T_all = {T_all}")


# =========================================================
# 範圍控制
# =========================================================

# 太陽輪範圍
T_s_min = T_min
T_s_max = T_all - 2 * T_min

T_s_list = range(T_s_min, T_s_max + 1)

print(f"太陽齒數範圍 {T_s_min} ~ {T_s_max}")


# ---------------------------------------------------------
# 第一層行星齒範圍
# ---------------------------------------------------------

T_p1_min = T_min
T_p1_max = math.floor((T_all - T_min) / 2)

T_p1_list = range(T_p1_min, T_p1_max + 1)

print(f"第一行星齒數範圍 {T_p1_min} ~ {T_p1_max}")


# ---------------------------------------------------------
# 第二層行星齒範圍
# ---------------------------------------------------------

T_p2_min = T_min
T_p2_max = T_p1_max

T_p2_list = range(T_p2_min, T_p2_max + 1)

print(f"第二行星齒數範圍 {T_p2_min} ~ {T_p2_max}")


# ---------------------------------------------------------
# 齒圈範圍
# ---------------------------------------------------------

T_r_min = T_min * 3
T_r_max = T_all

T_r_list = range(T_r_min, T_r_max + 1)

print(f"齒圈齒數範圍 {T_r_min} ~ {T_r_max}")


# =========================================================
# 有效組合
# =========================================================

valid_combinations = []


# =========================================================
# 計數器
# =========================================================

count_size = 0
count_geometry = 0
count_phase = 0
count_periodic = 0
count_ratio = 0
count_all = 0


# =========================================================
# 四層搜尋
# =========================================================

for T_s in T_s_list:

    for T_r in T_r_list:

        for T_p1 in T_p1_list:

            for T_p2 in T_p2_list:

                # =================================================
                # 尺寸限制
                # =================================================

                size_condition = (
                    2 * T_p1 + T_s <= T_all
                )


                # =================================================
                # 幾何限制
                # =================================================

                geometry_condition = (
                    T_s + T_p1 + T_p2 == T_r
                )


                # =================================================
                # 最大公因數
                # =================================================

                P = math.gcd(T_p1, T_p2)


                # =================================================
                # K 計算
                # =================================================

                K = (
                    T_s * T_p2
                    - T_r * T_p1
                ) / (3 * P)


                # =================================================
                # 相位限制
                # MATLAB:
                # mod(K,1) == 0
                # =================================================

                phase_condition = (
                    math.isclose(K, round(K), abs_tol=1e-10)
                )


                # =================================================
                # 週期限制
                # =================================================

                periodic_condition = (
                    P != 1
                )


                # =================================================
                # 減速比限制
                # =================================================

                z1 = T_p1 / T_s
                z2 = T_r / T_p2

                z_all = z1 * z2

                ratio_condition = (
                    z_all > z
                )


                # =================================================
                # 計數器
                # =================================================

                if size_condition:
                    count_size += 1

                if geometry_condition:
                    count_geometry += 1

                if phase_condition:
                    count_phase += 1

                if periodic_condition:
                    count_periodic += 1

                if ratio_condition:
                    count_ratio += 1


                # =================================================
                # 全部條件
                # =================================================

                if (
                    size_condition
                    and geometry_condition
                    and phase_condition
                    and periodic_condition
                    and ratio_condition
                ):

                    count_all += 1

                    valid_combinations.append([
                        T_s,
                        T_r,
                        T_p1,
                        T_p2,
                        z_all
                    ])


# =========================================================
# 輸出結果
# =========================================================

count_raw = (
    len(T_s_list)
    * len(T_r_list)
    * len(T_p1_list)
    * len(T_p2_list)
)


print("\n==============================")
print("搜尋結果")
print("==============================")

print(f"總數量: {count_raw}")
print(f"尺寸限制通過數量: {count_size}")
print(f"幾何限制通過數量: {count_geometry}")
print(f"相位限制通過數量: {count_phase}")
print(f"週期限制通過數量: {count_periodic}")
print(f"速比限制通過數量: {count_ratio}")
print(f"全部條件同時通過數量: {count_all}")


# =========================================================
# 顯示符合的組合
# =========================================================

if len(valid_combinations) == 0:

    print("\n沒有符合條件的組合")

else:

    print("\n符合所有限制的組合：")

    df = pd.DataFrame(
        valid_combinations,
        columns=[
            "T_s",
            "T_r",
            "T_p1",
            "T_p2",
            "z"
        ]
    )

    print(df.to_string(index=False))


import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

# =========================================================
# Output path
# =========================================================

OUTPUT_DIR = Path(__file__).resolve().parent

result_plot_path = OUTPUT_DIR / "gear_ratio_search_result.png"


# =========================================================
# 搜尋結果
# =========================================================

print("\n==============================")
print("搜尋結果")
print("==============================")

print(f"總數量: {count_raw}")
print(f"尺寸限制通過數量: {count_size}")
print(f"幾何限制通過數量: {count_geometry}")
print(f"相位限制通過數量: {count_phase}")
print(f"週期限制通過數量: {count_periodic}")
print(f"速比限制通過數量: {count_ratio}")
print(f"全部條件同時通過數量: {count_all}")


# =========================================================
# 建立結果 DataFrame
# =========================================================

if len(valid_combinations) > 0:

    df = pd.DataFrame(
        valid_combinations,
        columns=[
            "T_s",
            "T_r",
            "T_p1",
            "T_p2",
            "z"
        ]
    )

else:

    df = pd.DataFrame(
        columns=[
            "T_s",
            "T_r",
            "T_p1",
            "T_p2",
            "z"
        ]
    )


# =========================================================
# 建立 PNG 報告
# =========================================================

fig, ax = plt.subplots(
    figsize=(12, 7)
)

ax.axis("off")


# =========================================================
# 標題
# =========================================================

ax.text(
    0.5,
    0.95,
    "Planetary Gear Tooth Combination Search",
    ha="center",
    va="top",
    fontsize=18,
    fontweight="bold"
)


# =========================================================
# 搜尋統計
# =========================================================

statistics_text = (
    f"Total combinations        : {count_raw:,}\n"
    f"Size condition passed     : {count_size:,}\n"
    f"Geometry condition passed : {count_geometry:,}\n"
    f"Phase condition passed    : {count_phase:,}\n"
    f"Periodic condition passed : {count_periodic:,}\n"
    f"Ratio condition passed    : {count_ratio:,}\n"
    f"All conditions passed     : {count_all:,}"
)

ax.text(
    0.05,
    0.8,
    statistics_text,
    ha="left",
    va="top",
    fontsize=16,
    family="monospace"
)


# =========================================================
# 顯示有效組合
# =========================================================

if len(df) == 0:

    ax.text(
        0.5,
        0.45,
        "No valid combinations found",
        ha="center",
        va="center",
        fontsize=12
    )

else:

    # 只顯示前幾筆
    display_df = df.copy()

    # 齒比限制小數位
    display_df["z"] = display_df["z"].round(3)

    table = ax.table(
        cellText=display_df.values,
        colLabels=display_df.columns,
        cellLoc="center",
        loc="bottom"
    )

    table.auto_set_font_size(False)
    table.set_fontsize(10)

    # 調整表格大小
    table.scale(
        1.2,
        1.5
    )


# =========================================================
# Parameters
# =========================================================

parameter_text = (
    f"Module M = {M} mm\n"
    f"Minimum teeth = {T_min}\n"
    f"Maximum diameter = {D_max} mm\n"
    f"Target ratio = {z}"
)

ax.text(
    0.05,
    0.4,
    parameter_text,
    ha="left",
    va="top",
    fontsize=16,
    family="monospace"
)


# =========================================================
# Save
# =========================================================

fig.savefig(
    result_plot_path,
    dpi=200,
    bbox_inches="tight"
)

plt.close(fig)


print("\n==============================")
print("PNG report generated")
print("==============================")
print(f"Saved to: {result_plot_path}")