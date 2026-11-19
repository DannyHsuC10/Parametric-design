import numpy as np
import matplotlib.pyplot as plt
from Pacejka_tire_model.model import api as tire
from tire_data import tire_data
from pathlib import Path
from tire_data import tire_data

# 取得目前這個 .py 檔案所在資料夾
base_dir = Path(__file__).resolve().parent.parent
# 建立物件
tire_info = tire_data()
tire_info.load_json(base_dir/"tire.json")

print("==================================================")
print("mu")
print("==================================================")
# =====================================================
# Load tire
# =====================================================
tir_params = tire.load_tir("tire.tir")
SA = 0.0
IA = tire_info.camber
P = tire_info.Tire_Pressure
# =====================================================
# Sweep Range
# =====================================================
Fz_list = np.linspace(100, 1400, 8)      # N
SL_list = np.linspace(0, 1, 101)      # Slip Ratio
SA_list = np.linspace(0, 10, 101)      # Side Slip Angle

# =====================================================
# Plot Mux
# =====================================================
plt.figure(figsize=(8,6))

for Fz in Fz_list:

    mu_list = []

    for SL in SL_list:

        MF = tire.CalculationInput(
            FZ=Fz,
            SA=SA,
            SL=SL,
            IA=IA,
            pressure=P,
            tir_params=tir_params
        )

        Fx = tire.MF_Universal_solver("FX", MF)

        mu = Fx / Fz

        mu_list.append(mu)

    plt.plot(SL_list, mu_list, label=f"Fz={Fz:.0f}N")

plt.xlabel("Slip Ratio")
plt.ylabel("Longitudinal Friction Coefficient μx")
plt.title("μx vs Slip Ratio")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig(base_dir / "Figures" / "μx_vs_Slip_Ratio.png")
print("μx vs Slip Ratio plot saved.")
# =====================================================
# Plot Muy
# =====================================================
SL = 0.0
plt.figure(figsize=(8,6))

for Fz in Fz_list:

    mu_list = []

    for SA in SA_list:

        MF = tire.CalculationInput(
            FZ=Fz,
            SA=SA,
            SL=SL,
            IA=IA,
            pressure=P,
            tir_params=tir_params
        )

        Fy = tire.MF_Universal_solver("FY", MF)

        mu = Fy / Fz

        mu_list.append(mu)

    plt.plot(SA_list, mu_list, label=f"Fz={Fz:.0f}N")

plt.xlabel("Slip Angle (rad)")
plt.ylabel("Lateral Friction Coefficient μy")
plt.title("μy vs Slip Angle")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig(base_dir / "Figures" / "μy_vs_Slip_Angle.png")
print("μy vs Slip Angle plot saved.")

if tire_info.show_plt:
    plt.show()
else:
    plt.close('all')
