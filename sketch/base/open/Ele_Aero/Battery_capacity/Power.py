import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# =====================================================
# Path
# =====================================================

current_dir = Path(__file__).parent

file_path = current_dir / "fsae_australasia_lapsim.csv"

# =====================================================
# Read CSV
# =====================================================

df = pd.read_csv(file_path)

# =====================================================
# Data
# =====================================================

F = df["force"].to_numpy()
V = df["speed"].to_numpy()
t = df["time"].to_numpy()

# 只保留驅動力
F = np.where(F > 0, F, 0)

# =====================================================
# Power
# =====================================================

P = F * V

max_power = np.max(P)
avg_power = np.mean(P)

print(f"Maximum Power : {max_power:.1f} W")
print(f"Average Power : {avg_power:.1f} W")

# =====================================================
# Export CSV
# =====================================================

output_df = pd.DataFrame({
    "time": t,
    "power": P
})

csv_path = current_dir / "power_vs_time.csv"

output_df.to_csv(
    csv_path,
    index=False
)

print(f"CSV Saved : {csv_path}")

# =====================================================
# Plot
# =====================================================

plt.figure(
    figsize=(10,5)
)

plt.plot(
    t,
    P,
    linewidth=2,
    label="Power"
)

plt.grid(True)

plt.xlabel("Time (s)")
plt.ylabel("Power (W)")

plt.title("Power vs Time")

plt.legend()

plt.tight_layout()

plot_path = current_dir / "power_vs_time.png"

plt.savefig(
    plot_path,
    dpi=300
)

plt.show()

print(f"Figure Saved : {plot_path}")