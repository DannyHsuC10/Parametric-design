import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")

SF = 1.5
eta = param.eta

# === 讀取 csv ===

current_dir = Path(__file__).parent

file_path = current_dir / "fsae_australasia_lapsim.csv"

df = pd.read_csv(file_path)

# === 取出資料 ===
F = df["force"].values        # 力 (N)
x = df["position"].values    # 位移 (m)

# ==========================================================
# Energy Integration
# ==========================================================

energy = np.zeros(len(x))

W = 0.0

for i in range(len(F)-1):

    F1 = max(F[i], 0)
    F2 = max(F[i+1], 0)

    dx = x[i+1] - x[i]

    dW = (F1 + F2) / 2 * dx

    W += dW

    energy[i+1] = W

energy /= eta

W = energy[-1]

print(f"Single Lap Energy : {W:.2f} J")

E = W * 18

E_battery = E * SF

print(f"Total Energy : {E:.2f} J")
print(f"Battery Energy ({SF} SF): {E_battery:.2f} J")
print(f"Battery Energy : {E_battery/3.6e6:.2f} kWh")
print(f"電池需求能量({SF}安全係數): {E_battery/3.6/10**6:.2f} 度")
# ==========================================================
# Plot Energy vs Time
# ==========================================================

plt.figure(figsize=(10,5))

plt.plot(
    df["time"],
    energy,
    linewidth=2
)

plt.grid(True)

plt.xlabel("Time (s)")
plt.ylabel("Energy (J)")

plt.title(f"Accumulated Energy ({E_battery/3.6e6:.2f} kWh) vs Time")

plt.tight_layout()

plt.savefig(
    current_dir / "energy_vs_time.png",
    dpi=300
)

plt.show()