import numpy as np
import matplotlib.pyplot as plt
from Pacejka_tire_model.model import api as tire
from matplotlib.patches import Patch
from pathlib import Path
from tire_data import tire_data
"""
由於Fx的TTC資料不足所以使用Fy資料作為參考
"""

# 取得目前這個 .py 檔案所在資料夾
base_dir = Path(__file__).resolve().parent.parent
tir_params = tire.load_tir("tire.tir")
tire_info = tire_data()
tire_info.load_json(base_dir/"tire.json")
print("==================================================")
print("Tire_camber")
print("==================================================")
# ============================================================
# Sweep Settings
# ============================================================

SL_range = np.linspace(-1, 1, 61)
SA_range = np.linspace(-10, 10, 61)
FZ_range = np.linspace(0, 1400, 61)

SA = 0.0
SL = 0.0
IA = 0.0

# 固定最佳胎壓 (上一章分析結果)
pressure = tire_info.Tire_Pressure

IA_list = [-4,-2,0,2,4]

colors = [
    "red",
    "yellow",
    "green",
    "blue",
    "violet"
]
# ============================================================
# Plot
# ============================================================
# Fx
"""


SL_grid, FZ_grid = np.meshgrid(SL_range, FZ_range)

fig = plt.figure(figsize=(10,8))
ax = fig.add_subplot(111, projection="3d")

Fx_surface = []

for IA, color in zip(IA_list, colors):

    Fx = np.zeros_like(SL_grid)

    for i, FZ in enumerate(FZ_range):

        for j, SL in enumerate(SL_range):

            MF = tire.CalculationInput(
                FZ=FZ,
                SA=SA,
                SL=SL,
                IA=IA,
                pressure=pressure,
                tir_params=tir_params
            )

            Fx[i,j] = tire.MF_Universal_solver("FX", MF)

    Fx_surface.append(Fx.copy())

    ax.plot_surface(
        FZ_grid,
        SL_grid,
        Fx,
        color=color,
        alpha=0.25,
        linewidth=0
    )

legend_elements = [
    Patch(facecolor=c, label=f"{ia}°")
    for ia,c in zip(IA_list,colors)
]

ax.legend(handles=legend_elements, loc="upper left")

ax.set_xlabel("Normal Load Fz (N)")
ax.set_ylabel("Slip Ratio")
ax.set_zlabel("Longitudinal Force Fx (N)")
ax.set_title("Magic Formula Tire Fx Surface vs Camber")

plt.tight_layout()
plt.savefig(current_dir/"Figures"/"Magic_Formula_Tire_Fx_Surface_vs_Camber.png")

"""
# ============================================================
# Fy
SA = 0.0
SL = 0.0
IA = 0.0
SA_grid, FZ_grid = np.meshgrid(SA_range, FZ_range)

fig = plt.figure(figsize=(10,8))
ax = fig.add_subplot(111, projection="3d")

Fy_surface = []

for IA, color in zip(IA_list, colors):

    Fy = np.zeros_like(SA_grid)

    for i, FZ in enumerate(FZ_range):

        for j, SA in enumerate(SA_range):

            MF = tire.CalculationInput(
                FZ=FZ,
                SA=SA,
                SL=SL,
                IA=IA,
                pressure=pressure,
                tir_params=tir_params
            )

            Fy[i,j] = tire.MF_Universal_solver("FY", MF)

    Fy_surface.append(Fy.copy())

    ax.plot_surface(
        FZ_grid,
        SA_grid,
        Fy,
        color=color,
        alpha=0.25,
        linewidth=0
    )

legend_elements = [
    Patch(facecolor=c, label=f"{ia}°")
    for ia,c in zip(IA_list,colors)
]

ax.legend(handles=legend_elements, loc="upper left")

ax.set_xlabel("Normal Load Fz (N)")
ax.set_ylabel("Slip Angle (deg)")
ax.set_zlabel("Lateral Force Fy (N)")
ax.set_title("Magic Formula Tire Fy Surface vs Camber")

plt.tight_layout()
plt.savefig(base_dir/"Figures"/"Magic_Formula_Tire_Fy_Surface_vs_Camber.png")
print("Magic_Formula_Tire_Fy_Surface_vs_Camber saved to Figures folder")
# ===========================
# RMS
# ===========================
"""
# Fx
Fx_surface = np.array(Fx_surface)

rms_list = []

for surface in Fx_surface:

    rms = np.sqrt(np.mean(surface**2))
    rms_list.append(rms)

best_idx = np.argmax(rms_list)

print("===================================")
print("Best Camber")
print("-----------------------------------")
print(f"IA = {IA_list[best_idx]} deg")
print(f"RMS Fx = {rms_list[best_idx]:.3f}")

plt.figure(figsize=(6,4))

plt.plot(
    IA_list,
    rms_list,
    marker="o",
    linewidth=2
)

plt.grid(True)

plt.xlabel("Camber Angle IA (deg)")
plt.ylabel("RMS Fx (N)")
plt.title("Tire Performance vs Camber")

plt.tight_layout()
plt.savefig(current_dir/"Figures"/"Tire_Performance_vs_Camber_RMS.png")

"""
# ==============================
# Fy
Fy_surface = np.array(Fy_surface)

rms_list = []

for surface in Fy_surface:

    rms = np.sqrt(np.mean(surface**2))
    rms_list.append(rms)

best_idx = np.argmax(rms_list)

print("===================================")
print("Best Camber")
print("-----------------------------------")
print(f"IA = {IA_list[best_idx]} deg")
print(f"RMS Fy = {rms_list[best_idx]:.3f}")

plt.figure(figsize=(6,4))

plt.plot(
    IA_list,
    rms_list,
    marker="o",
    linewidth=2
)

plt.grid(True)

plt.xlabel("Camber Angle IA (deg)")
plt.ylabel("RMS Fy (N)")
plt.title("Tire Performance vs Camber")

plt.tight_layout()
plt.savefig(base_dir/"Figures"/"Tire_Performance_vs_Camber_RMS.png")
print("Tire_Performance_vs_Camber_RMS saved to Figures folder")


if tire_info.show_plt:
    plt.show()
else:
    plt.close('all')

# ============================
# save
# ============================

# Fy擬合資訊較完整存Fy資料
# 建立物件

tire_info.camber = IA_list[best_idx]

tire_info.save_json(base_dir / "tire.json")

