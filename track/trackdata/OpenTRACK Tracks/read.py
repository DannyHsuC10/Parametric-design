import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

current_dir = Path(__file__).resolve().parent

with np.load(current_dir / "OpenTRACK_FSAE_A_24_Closed_Forward.npz") as data:
    print(data.files)

    # 取出某個陣列，例如 'X'
    X = data["X"]
    Y = data["Y"]

    # 也可以取出其他資訊
    info_name = data["info_name"]

fig, ax = plt.subplots(figsize=(10, 8), constrained_layout=True)
ax.plot(X, Y, color="#1f77b4", linewidth=2)
ax.set_aspect("equal", adjustable="box")
ax.set_title(f"{info_name} XY Map")
ax.set_xlabel("X [m]")
ax.set_ylabel("Y [m]")
ax.grid(True, alpha=0.3)

output_path = current_dir / f"{info_name}_read_xy_map.png"
#plt.savefig(output_path, format="png", dpi=180)
plt.show()
plt.close(fig)

print(f"XY map saved: {output_path}")

