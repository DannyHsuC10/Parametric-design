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

SA_range = np.linspace(-10, 10, 81)
FZ_range = np.linspace(0, 1400, 61)

SL = 0.0
IA = tire_info.camber
P = tire_info.Tire_Pressure


# ============================================================
# Calculate Fy Surface
# ============================================================

SA_grid, FZ_grid = np.meshgrid(SA_range, FZ_range)

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

# ============================================================
# Plot Fy Surface
# ============================================================

fig = plt.figure(figsize=(9,7))
ax = fig.add_subplot(111, projection='3d')

surf = ax.plot_surface(
    np.rad2deg(SA_grid),
    FZ_grid,
    Fy,
    cmap="viridis"
)

ax.set_xlabel("Slip Angle (deg)")
ax.set_ylabel("Normal Load Fz (N)")
ax.set_zlabel("Lateral Force Fy (N)")
ax.set_title("Magic Formula Tire Fy Surface")

fig.colorbar(surf)

plt.tight_layout()
plt.savefig(base_dir / "Figures" / "Magic Formula Tire Fy Surface.png")
print("Magic Formula Tire Fy Surface plot saved.")
# ============================================================
# Peak Force
# ============================================================

idx = np.argmax(np.abs(Fy), axis=1)

Fy_max = Fy[np.arange(len(FZ_range)), idx]
SA_peak = SA_range[idx]


plt.figure(figsize=(6,4))
plt.plot(FZ_range,np.abs(Fy_max),linewidth=2)

plt.xlabel("Fz (N)")
plt.ylabel("Peak Fy (N)")
plt.title("Peak Fy vs Fz")
plt.grid(True)
plt.savefig(base_dir / "Figures" / "Peak Fy vs Fz.png")
print("Peak Fy vs Fz plot saved.")
# ============================================================
# Peak Slip Angle
# ============================================================

plt.figure(figsize=(6,4))

plt.plot(
    FZ_range,
    np.rad2deg(SA_peak),
    linewidth=2
)

plt.xlabel("Fz (N)")
plt.ylabel("Peak Slip Angle (deg)")
plt.title("Peak Slip Angle vs Fz")
plt.grid(True)
plt.savefig(base_dir / "Figures" / "Peak Slip Angle vs Fz.png")
print("Peak Slip Angle vs Fz plot saved.")
# ============================================================
# Linear Regression Through Origin
# ============================================================

mask = FZ_range > 0

FZ_fit = FZ_range[mask]
Fy_fit = np.abs(Fy_max[mask])

mu_y = np.sum(FZ_fit * Fy_fit) / np.sum(FZ_fit**2)

Fy_linear = mu_y * FZ_fit

plt.figure(figsize=(6,4))

plt.plot(
    FZ_fit,
    Fy_fit,
    'o',
    label='Magic Formula'
)

plt.plot(
    FZ_fit,
    Fy_linear,
    linewidth=2,
    label=f'Linear Fit (μ={mu_y:.3f})'
)

plt.xlabel("Normal Load Fz (N)")
plt.ylabel("Peak Fy (N)")
plt.title("Linear Regression Through Origin")
plt.grid(True)
plt.legend()
plt.savefig(base_dir / "Figures" / "Linear Regression Through Origin Fy.png")
print("Linear Regression Through Origin Fy plot saved.")
# ============================================================
# Peak Friction Coefficient
# ============================================================

mu_curve = Fy_fit / FZ_fit

mu_y_max = np.max(mu_curve)

plt.figure(figsize=(6,4))

plt.plot(
    FZ_fit,
    mu_curve,
    linewidth=2
)

plt.xlabel("Normal Load Fz (N)")
plt.ylabel("Peak μy")
plt.title("Peak Friction Coefficient")
plt.grid(True)
plt.savefig(base_dir / "Figures" / "Peak Friction Coefficient Fy.png")
print("Peak Friction Coefficient Fy plot saved.")
# ============================================================
# Print Results
# ============================================================

print("="*40)
print(f"Linear Regression μy : {mu_y:.4f}")
print(f"Maximum μy           : {mu_y_max:.4f}")
print("="*40)

if tire_info.show_plt:
    plt.show()
else:
    plt.close('all')


# ============================================================
# Save to json
# ============================================================


tire_info.mu_y_RL = mu_y # 回歸
tire_info.mu_y_max = mu_y_max # 最大值

tire_info.save_json(base_dir / "tire.json")

