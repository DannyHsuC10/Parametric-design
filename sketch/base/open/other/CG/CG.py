import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ==========================================
# Output path (same folder as this script)
# ==========================================
OUTPUT_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = OUTPUT_DIR / "FSAE_CG_Height_Limit.png"

SF = 1.1

# ==========================================
# Parameters
# ==========================================
track_width = np.linspace(0.8, 1.6, 300)  # m

theta_45 = np.deg2rad(45)
theta_60 = np.deg2rad(60)

# ==========================================
# Calculate maximum CG height
# h = t / (2*tan(theta))
# ==========================================
h_45 = track_width / (2 * np.tan(theta_45))/SF
h_60 = track_width / (2 * np.tan(theta_60))/SF

# ==========================================
# Plot
# ==========================================
plt.figure(figsize=(8, 6))

plt.plot(track_width, h_45, label="Tilt Angle = 45°", linewidth=2)
plt.plot(track_width, h_60, label="Tilt Angle = 60°", linewidth=2)

# Mark common FSAE track widths
for t in [1.2, 1.25, 1.3]:
    plt.axvline(t, linestyle="--", alpha=0.4)

plt.xlabel("Track Width (m)")
plt.ylabel("Maximum CG Height (m)")
plt.title("Maximum Allowable CG Height for FSAE Tilt Test")
plt.grid(True)
plt.legend()

plt.tight_layout()

# Save figure
plt.savefig(OUTPUT_FILE, dpi=300)

plt.show()

print(f"Figure saved to:\n{OUTPUT_FILE}")