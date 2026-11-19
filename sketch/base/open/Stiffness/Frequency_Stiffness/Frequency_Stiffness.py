import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")

OUTPUT_DIR = Path(__file__).parent

# Parameters
m = param.ms/2      # Quarter-car sprung mass (kg)

highlight_k = [param.Kr_roll,param.Kr_heave]

# Spring stiffness range
k = np.linspace(10000, 100000, 5000)    # N/m



# 計算
#=====================================
# Natural frequency
def natural_frequency(k,m):
    fn = (1 / (2 * np.pi)) * np.sqrt(k / m)
    return fn

fn = natural_frequency(k,m)#這邊計算應該要用ride rate

# =====================================
# Plot
plt.figure(figsize=(8, 5))

plt.plot(k / 1000,fn,linewidth=2)

for ki in highlight_k:
    fi = natural_frequency(ki,m)
    plt.scatter(ki / 1000, fi, color="red", zorder=5)

    plt.annotate(
        f"{fi:.2f} Hz",
        (ki / 1000, fi),
        xytext=(6, 8),
        textcoords="offset points"
    )

plt.grid(True)

plt.xlabel("Spring Stiffness (kN/m)")
plt.ylabel("Natural Frequency (Hz)")
plt.title("Natural Frequency vs Spring Stiffness")

plt.tight_layout()

# Save figure
output_path = OUTPUT_DIR / "Natural_Frequency_vs_Spring_Stiffness.png"

plt.savefig(output_path,dpi=300)

print(f"Figure saved to:\n{output_path}")

plt.show()



