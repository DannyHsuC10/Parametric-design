import numpy as np
import matplotlib.pyplot as plt
from Pacejka_tire_model.model import api as tire
from tire_data import tire_data
from pathlib import Path


# 取得目前這個 .py 檔案所在資料夾
base_dir = Path(__file__).resolve().parent.parent
# 建立物件
tire_info = tire_data()
tire_info.load_json(base_dir/"tire.json")

tir_params = tire.load_tir("tire.tir")

# ============================================================
# Sweep Settings
# ============================================================

SL_range = np.linspace(-1, 1, 61)
FZ_range = np.linspace(0, 1400, 61)

SA = 0.0
IA = tire_info.camber
P = tire_info.Tire_Pressure


# ============================================================
# Calculate Fx Surface
# ============================================================

SL_grid, FZ_grid = np.meshgrid(SL_range, FZ_range)

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

# ============================================================
# Plot Fx Surface
# ============================================================

fig = plt.figure(figsize=(9,7))
ax = fig.add_subplot(111, projection='3d')

surf = ax.plot_surface(
    SL_grid,
    FZ_grid,
    Fx,
    cmap="viridis"
)

ax.set_xlabel("Slip Ratio")
ax.set_ylabel("Normal Load Fz (N)")
ax.set_zlabel("Longitudinal Force Fx (N)")
ax.set_title("Magic Formula Tire Fx Surface")

fig.colorbar(surf)
plt.tight_layout()
plt.savefig(base_dir / "Figures" / "Magic Formula Tire Fx Surface.png")
print("Fx surface plot saved to Figures folder.")
# ============================================================
# Peak Force
# ============================================================

idx = np.argmax(Fx, axis=1)

Fx_max = Fx[np.arange(len(FZ_range)), idx]
SL_peak = SL_range[idx]

plt.figure(figsize=(6,4))
plt.plot(FZ_range, Fx_max, linewidth=2)

plt.xlabel("Fz (N)")
plt.ylabel("Peak Fx (N)")
plt.title("Peak Fx vs Fz")
plt.grid(True)
plt.savefig(base_dir / "Figures" / "Peak Fx vs Fz.png")

plt.figure(figsize=(6,4))
plt.plot(FZ_range, SL_peak, linewidth=2)

plt.xlabel("Fz (N)")
plt.ylabel("Peak Slip Ratio")
plt.title("Peak Slip Ratio vs Fz")
plt.grid(True)
plt.tight_layout()
plt.savefig(base_dir / "Figures" / "Peak Slip Ratio vs Fz.png")
print("Peak Fx and Peak Slip Ratio plots saved to Figures folder.")
# ============================================================
# Linear Regression Through Origin
# ============================================================

# 去除 Fz = 0
mask = FZ_range > 0

FZ_fit = FZ_range[mask]
Fx_fit = Fx_max[mask]

# 最小平方且固定通過原點
mu_x = np.sum(FZ_fit * Fx_fit) / np.sum(FZ_fit**2)

Fx_linear = mu_x * FZ_fit

plt.figure(figsize=(6,4))

plt.plot(FZ_fit, Fx_fit, 'o', label='Magic Formula')
plt.plot(FZ_fit, Fx_linear,
         linewidth=2,
         label=f'Linear Fit (μ={mu_x:.3f})')

plt.xlabel("Normal Load Fz (N)")
plt.ylabel("Peak Fx (N)")
plt.title("Linear Regression Through Origin")
plt.grid(True)
plt.legend()
plt.savefig(base_dir / "Figures" / "Linear Regression Through Origin Fx.png")
print("Linear Regression Through Origin plot saved to Figures folder.")
# ============================================================
# Peak Friction Coefficient
# ============================================================

mu_curve = Fx_fit / FZ_fit

mu_x_max = np.max(mu_curve)

plt.figure(figsize=(6,4))

plt.plot(FZ_fit, mu_curve, linewidth=2)

plt.xlabel("Normal Load Fz (N)")
plt.ylabel("Peak μx")
plt.title("Peak Friction Coefficient")
plt.grid(True)
plt.savefig(base_dir / "Figures" / "Peak Friction Coefficient Fx.png")
print("Peak Friction Coefficient plot saved to Figures folder.")
# ============================================================
# Print Results
# ============================================================

print("="*40)
print(f"Linear Regression μx : {mu_x:.4f}")
print(f"Maximum μx           : {mu_x_max:.4f}")
print("="*40)

if tire_info.show_plt:
    plt.show()
else:
    plt.close('all')

# 修改參數
tire_info.mu_x_RL = mu_x # 回歸
tire_info.mu_x_max = mu_x_max # 最大值
# 存成 json
tire_info.save_json(base_dir / "tire.json")
print("Updated tire.json with new μx values.")

