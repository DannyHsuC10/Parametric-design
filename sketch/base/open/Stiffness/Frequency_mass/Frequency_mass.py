import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")


OUTPUT_DIR = Path(__file__).parent


# Parameters
# =====================================
m_total = param.m / 4      # Total quarter-car mass (kg)

Ks = param.Ks           # Spring stiffness (N/m)
Kt = param.Kt          # Tire stiffness (N/m)
MR = param.MR              # Motion ratio

target_ratio = param.mu/m_total# 目前簧下比
print(f"Target unsprung mass ratio: {target_ratio:.2f}")

mu_ratio = np.linspace(0.05, 0.50, 500)

# 計算
# =====================================
# Wheel rate / Ride rate

Kw = Ks * MR**2
Kr = (Kw * Kt) / (Kw + Kt)



mu = m_total * mu_ratio
ms = m_total - mu

# Natural frequencies (RCVD)
fn_sprung = (1 / (2 * np.pi)) * np.sqrt(Kr / ms)

fn_unsprung = (1 / (2 * np.pi)) * np.sqrt((Kt + Kw) / mu)


# Plot
# =====================================

plt.figure(figsize=(8,5))

plt.plot(
    mu_ratio * 100,
    fn_sprung,
    linewidth=2,
    label="Sprung Mass Mode"
)

plt.plot(
    mu_ratio * 100,
    fn_sprung * 5,
    linewidth=2,
    label="5 times line"
)

plt.plot(
    mu_ratio * 100,
    fn_sprung * 3,
    linewidth=2,
    label="3 times line"
)

plt.plot(
    mu_ratio * 100,
    fn_unsprung,
    linewidth=2,
    label="Unsprung Mass Mode"
)

# 目標比例計算
# ===========================================================
idx = np.argmin(np.abs(mu_ratio - target_ratio))

x = mu_ratio[idx] * 100

fs = fn_sprung[idx]
fu = fn_unsprung[idx]

print(f"Unsprung ratio : {x:.1f}%")
print(f"Sprung frequency : {fs:.2f} Hz")
print(f"Wheel hop frequency : {fu:.2f} Hz")

# Sprung mode
plt.scatter(
    x,
    fs,
    color="red",
    zorder=5
)

plt.annotate(
    f"{fs:.2f} Hz",
    (x, fs),
    xytext=(8, 10),
    textcoords="offset points",
    color="red"
)

# Unsprung mode
plt.scatter(
    x,
    fu,
    color="blue",
    zorder=5
)

plt.annotate(
    f"{fu:.2f} Hz",
    (x, fu),
    xytext=(8, -18),
    textcoords="offset points",
    color="blue"
)


plt.grid(True)

plt.xlabel("Unsprung Mass Ratio (%)")
plt.ylabel("Natural Frequency (Hz)")
plt.title("Natural Frequency vs Unsprung Mass Ratio")

plt.legend()

plt.tight_layout()


# Save figure
# =====================================

output_path = OUTPUT_DIR / "Natural_Frequency_vs_Unsprung_Mass_Ratio.png"

plt.savefig(
    output_path,
    dpi=300,
    bbox_inches="tight"
)

print(f"Figure saved to:\n{output_path}")

plt.show()