import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")

OUTPUT_DIR = Path(__file__).resolve().parent

csv_path = OUTPUT_DIR / "brake_line_data.csv"

low_plot_path = OUTPUT_DIR / "Low_Expansion_Tube.png"
high_plot_path = OUTPUT_DIR / "High_Expansion_Tube.png"

# 參數設定
# ====================================
# Read CSV
df = pd.read_csv(csv_path)

print("\nLoaded brake line data:")
print(df)


pressure_target = param.P_brake# 目標壓力

# 計算
# =====================================
# Low expansion tube
low_data = df[df["type"] == "Low"]

pl = low_data["pressure_MPa"].to_numpy()
cl = low_data["expansion_mm3_per_m"].to_numpy()

# 2nd-order polynomial fitting
nl = np.polyfit(pl, cl, 2)

# Fitted curve
pl_fit = np.arange(0, 20.1, 0.1)
cl_fit = np.polyval(nl, pl_fit)


cl_target = np.polyval(nl, pressure_target)

print("\n===== Low Expansion Tube =====")

print(f"Polynomial coefficients:")
print(nl)

print(
    f"Expansion @ {pressure_target:.2f} MPa = "
    f"{cl_target:.2f} mm^3/m"
)

# plot
# =====================================
# Plot Low Expansion
plt.figure(figsize=(8, 5))

plt.scatter(
    pl,
    cl,
    s=60,
    label="Measured Data"
)

plt.plot(
    pl_fit,
    cl_fit,
    linewidth=2,
    label="2nd Order Polynomial Fit"
)

# Target point
plt.scatter(
    pressure_target,
    cl_target,
    s=80,
    label=f"{pressure_target:.2f} MPa"
)

plt.grid(True)

plt.xlabel("Tube Internal Pressure (MPa)")
plt.ylabel("Expansion Coefficient (mm³/m)")

plt.title("Low Expansion Tube Standard")

plt.legend()

plt.tight_layout()

plt.savefig(
    low_plot_path,
    dpi=300,
    bbox_inches="tight"
)

print(f"Low expansion plot saved to:")
print(low_plot_path)

plt.show()

# 計算
# =====================================
# High expansion tube

high_data = df[df["type"] == "High"]

ph = high_data["pressure_MPa"].to_numpy()
ch = high_data["expansion_mm3_per_m"].to_numpy()

# 2nd-order polynomial fitting
nh = np.polyfit(ph, ch, 2)

# Fitted curve
ph_fit = np.arange(0, 20.1, 0.1)
ch_fit = np.polyval(nh, ph_fit)

# Evaluate
ch_target = np.polyval(nh, pressure_target)

print("\n===== High Expansion Tube =====")

print(f"Polynomial coefficients:")
print(nh)

print(
    f"Expansion @ {pressure_target:.2f} MPa = "
    f"{ch_target:.2f} mm^3/m"
)

# Plot High Expansion
# =====================================

plt.figure(figsize=(8, 5))

plt.scatter(
    ph,
    ch,
    s=60,
    label="Measured Data"
)

plt.plot(
    ph_fit,
    ch_fit,
    linewidth=2,
    label="2nd Order Polynomial Fit"
)

# Target point
plt.scatter(
    pressure_target,
    ch_target,
    s=80,
    label=f"{pressure_target:.2f} MPa"
)

plt.grid(True)

plt.xlabel("Tube Internal Pressure (MPa)")
plt.ylabel("Expansion Coefficient (mm³/m)")

plt.title("High Expansion Tube Standard")

plt.legend()

plt.tight_layout()

plt.savefig(
    high_plot_path,
    dpi=300,
    bbox_inches="tight"
)

print(f"High expansion plot saved to:")
print(high_plot_path)

plt.show()