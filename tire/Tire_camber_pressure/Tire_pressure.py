import numpy as np
import matplotlib.pyplot as plt
from Pacejka_tire_model.model import api as tire
from matplotlib.patches import Patch
from pathlib import Path
from tire_data import tire_data
# 取得目前這個 .py 檔案所在資料夾
base_dir = Path(__file__).resolve().parent.parent

tire_info = tire_data()
tire_info.load_json(base_dir/"tire.json")
tir_params = tire.load_tir("tire.tir")

print("==================================================")
print("Tire_pressure")
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


psi_list = [8, 9, 10, 11, 12, 13, 14]
pressure_list = [psi * 6894.757293168 for psi in psi_list]

colors = [
    "red",
    "orange",
    "yellow",
    "green",
    "blue",
    "indigo",
    "violet"
]

SL_grid, FZ_grid = np.meshgrid(SL_range, FZ_range)
# ============================================================
# Plot
# ============================================================
"""
fig = plt.figure(figsize=(10,8))
ax = fig.add_subplot(111, projection="3d")

Fx_surface = []
# Fx ========================================
for psi, P, color in zip(psi_list, pressure_list, colors):

    Fx = np.zeros_like(SL_grid)

    for i, FZ in enumerate(FZ_range):
        for j, SL in enumerate(SL_range):

            MF = tire.CalculationInput(
                FZ=FZ,
                SA=SA,
                SL=SL,
                IA=IA,
                pressure=P,
                tir_params=tir_params
            )

            Fx[i, j] = tire.MF_Universal_solver("FX", MF)

    Fx_surface.append(Fx.copy())   # ⭐新增這行

    ax.plot_surface(
        SL_grid,
        FZ_grid,
        Fx,
        color=color,
        alpha=0.2,
        linewidth=0
    )

legend_elements = [
    Patch(facecolor=c, label=f"{psi} psi")
    for psi, c in zip(psi_list, colors)
]

ax.legend(handles=legend_elements, loc="upper left")

ax.set_xlabel("Slip Ratio")
ax.set_ylabel("Normal Load Fz (N)")
ax.set_zlabel("Longitudinal Force Fx (N)")
ax.set_title("Magic Formula Tire Fx Surface vs Pressure")

plt.tight_layout()
plt.savefig(current_dir/ "Figures" / "Magic_Formula_Tire_Fx_Surface_vs_Pressure.png")

"""
# Fy ===========================================
SA = 0.0
SL = 0.0
SA_grid, FZ_grid = np.meshgrid(SA_range, FZ_range)
fig = plt.figure(figsize=(10,8))
ax = fig.add_subplot(111, projection="3d")

Fy_surface = []
for psi, P, color in zip(psi_list, pressure_list, colors):

    Fy = np.zeros_like(SA_grid)

    for i, FZ in enumerate(FZ_range):
        for j, SA in enumerate(SA_range):

            MF = tire.CalculationInput(
                FZ=FZ,
                SA=SA,
                SL=SL,
                IA=IA,
                pressure=P,
                tir_params=tir_params
            )

            Fy[i, j] = tire.MF_Universal_solver("FY", MF)

    Fy_surface.append(Fy.copy())  

    ax.plot_surface(
        FZ_grid,
        SA_grid,
        Fy,
        color=color,
        alpha=0.2,
        linewidth=0
    )

legend_elements = [
    Patch(facecolor=c, label=f"{psi} psi")
    for psi, c in zip(psi_list, colors)
]

ax.legend(handles=legend_elements, loc="upper left")

ax.set_ylabel("Slip angle (deg)")
ax.set_xlabel("Normal Load Fz (N)")
ax.set_zlabel("Lateral Force Fy (N)")
ax.set_title("Magic Formula Tire Fy Surface vs Pressure")

plt.tight_layout()
plt.savefig(base_dir/ "Figures" / "Magic_Formula_Tire_Fy_Surface_vs_Pressure.png")
print("Magic_Formula_Tire_Fy_Surface_vs_Pressure saved to Figures folder")

# ===========================
# RMS
# ===========================
"""
# Fx
Fx_surface = np.array(Fx_surface)  # shape: (psi, FZ, SL)
rms_list = []

for i, psi in enumerate(psi_list):

    rms = np.sqrt(np.mean(Fx_surface[i]**2))
    rms_list.append(rms)

best_idxx = np.argmax(rms_list)

print("Best Pressure:")
print(f"{psi_list[best_idxx]} psi")
print(f"RMS Fx = {rms_list[best_idxx]:.3f}")

plt.figure()
plt.plot(psi_list, rms_list, marker="o")
plt.xlabel("Tire Pressure (psi)")
plt.ylabel("RMS Fx")
plt.title("Tire Performance vs Pressure (RMS Criterion)")
plt.grid()
plt.savefig(current_dir/ "Figures" / "Tire_Performance_vs_Pressure_RMS_Criterion.png")

"""
# =================================
# Fy
Fy_surface = np.array(Fy_surface)  # shape: (psi, FZ, SL)
rms_list = []

for i, psi in enumerate(psi_list):

    rms = np.sqrt(np.mean(Fy_surface[i]**2))
    rms_list.append(rms)

best_idxy = np.argmax(rms_list)

print("===================================")
print("Best Pressure:")
print("-----------------------------------")

print(f"{psi_list[best_idxy]} psi")
print(f"RMS Fy = {rms_list[best_idxy]:.3f}")

plt.figure()
plt.plot(psi_list, rms_list, marker="o")
plt.xlabel("Tire Pressure (psi)")
plt.ylabel("RMS Fy")
plt.title("Tire Performance vs Pressure (RMS Criterion)")
plt.grid()
plt.savefig(base_dir/ "Figures" / "Tire_Performance_vs_Pressure_RMS_Criterion_Fy.png")

print("Tire_Performance_vs_Pressure_RMS_Criterion_Fy saved to Figures folder")



# ============================
# save
# ============================

# Fy擬合資訊較完整存Fy資料
# 建立物件

if tire_info.show_plt:
    plt.show()
else:
    plt.close('all')

tire_info.load_json(base_dir/"tire.json")
# 修改參數
tire_info.Tire_Pressure = psi_list[best_idxy]*6894.757293168  # psi to Pa
# 存成 json
tire_info.save_json(base_dir/"tire.json")

