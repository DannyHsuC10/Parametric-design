import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")


mu_y = param.mu_y       # lateral friction coefficient
g = 9.81         # gravity (m/s^2)

R_list = np.linspace(3,50,200)

v_ext = []

for r in R_list:

    v = np.sqrt(
        mu_y * g * r
    )

    v_ext.append(v)

    print(
        f"半徑: {r:.2f} m >> "
        f"極限速度: {v*3.6:.2f} km/hr "
        f"({v:.2f} m/s)"
    )


v_ext = np.array(v_ext)

# ==========================================
# Plot
# ==========================================

plt.figure(figsize=(8,5))
plt.plot(
    R_list,
    v_ext * 3.6,
    linewidth=2)
plt.xlabel("Corner Radius R (m)")
plt.ylabel("Maximum Speed (km/h)")
plt.title(r"Cornering Speed Limit ($v=\sqrt{\mu_y g R}$)")
plt.grid(True)

# ==========================================
# Save figure
# ==========================================

save_path = (Path(__file__).parent /"cornering_speed_limit.png")

plt.savefig(
    save_path,
    dpi=300,
    bbox_inches="tight")


plt.show()
