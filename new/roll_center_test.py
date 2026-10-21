import numpy as np
import matplotlib.pyplot as plt

# -----------------------
# Parameters
# -----------------------
K_s = 1.0          # Suspension stiffness (normalized)
K_c = 10.0         # Chassis stiffness = 10x suspension

# Roll center height ratio (0~1 CG height)
rc_ratio = np.linspace(0, 1.0, 300)

# Fraction of roll moment through suspension
alpha = 1 - rc_ratio

# Equivalent stiffness
K_eq = alpha**2 * K_s + (1 - alpha)**2 * K_c

# Find minimum
idx = np.argmin(K_eq)

print("Minimum stiffness")
print(f"RC/CG = {rc_ratio[idx]:.3f}")
print(f"K_eq = {K_eq[idx]:.3f}")

# -----------------------
# Plot
# -----------------------
plt.figure(figsize=(8,5))

plt.plot(rc_ratio, K_eq, linewidth=2)

plt.scatter(rc_ratio[idx], K_eq[idx], color='red', zorder=5)

plt.xlabel("Roll Center Height / CG Height")
plt.ylabel("Equivalent Roll Stiffness (Normalized)")
plt.title("Equivalent Roll Stiffness vs Roll Center Height")

plt.grid(True)

plt.show()