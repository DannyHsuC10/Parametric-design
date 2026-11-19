import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")

# ==========================
# Main Spring
# ==========================
k_main = param.Ks  # N/m

# Tender = 30~70% of Main
ratio = np.linspace(0.3, 0.7, 100)
k_tender = ratio * k_main

# Equivalent stiffness
k_eq = (k_main * k_tender) / (k_main + k_tender)

# ==========================
# Plot 1
# ==========================
plt.figure(figsize=(8,5))
plt.plot(k_tender/1000, k_eq/1000, linewidth=2)

plt.xlabel("Tender Spring Stiffness (N/mm)")
plt.ylabel("Equivalent Stiffness (N/mm)")
plt.title("Series Spring Equivalent Stiffness")
plt.grid(True)
plt.tight_layout()

save_path_1 = Path(__file__).parent / "series_spring_equivalent_stiffness.png"
plt.savefig(
    save_path_1,
    dpi=300,
    bbox_inches="tight"
)

# ==========================
# Plot 2
# ==========================
plt.figure(figsize=(8,5))
plt.plot(ratio*100, k_eq/k_main*100, linewidth=2)

plt.xlabel("Tender Stiffness (% of Main)")
plt.ylabel("Equivalent Stiffness (% of Main)")
plt.title("Equivalent Stiffness Ratio")
plt.grid(True)
plt.tight_layout()

save_path_2 = Path(__file__).parent / "equivalent_stiffness_ratio.png"
plt.savefig(
    save_path_2,
    dpi=300,
    bbox_inches="tight"
)

print(f"Figure saved to: {save_path_1}")
print(f"Figure saved to: {save_path_2}")

plt.show()
