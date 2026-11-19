import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# =====================================
# Parameters
# =====================================

R = 0.20          # Radius (m)
E = 8e6           # Rubber Young's modulus (Pa)

V = 2.6e-3        # Volume (m^3)
m = 3.6           # Mass (kg)

rho = m / V       # Density (kg/m^3)

A = 2500e-6       # Cross-sectional area (m^2)
I = 1.78e-5       # Second moment of area (m^4)

mode_max = 5

# =====================================
# Calculate natural frequencies
# =====================================

freq = np.zeros(mode_max)

print("Mode   Frequency (Hz)")
print("----------------------")

for n in range(1, mode_max + 1):

    if n == 1:
        freq[n - 1] = 0.0
    else:
        omega = np.sqrt((E * I) / (rho * A * R**4)) * (n**2 * (n**2 - 1))
        freq[n - 1] = omega / (2 * np.pi)

    print(f"{n:2d}     {freq[n-1]:8.2f}")

# =====================================
# Plot
# =====================================

plt.figure(figsize=(8, 5))

plt.plot(
    np.arange(1, mode_max + 1),
    freq,
    "-o",
    linewidth=2,
    markersize=6
)

plt.grid(True)

plt.xlabel("Mode Number")
plt.ylabel("Frequency (Hz)")
plt.title("Tire Ring Mode Frequencies")

plt.tight_layout()

# =====================================
# Save figure
# =====================================

output_path = Path(__file__).parent / "Tire_Ring_Mode_Frequencies.png"

plt.savefig(output_path, dpi=300)

print(f"\nFigure saved to:\n{output_path}")

plt.show()