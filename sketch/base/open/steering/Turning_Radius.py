import numpy as np
import matplotlib.pyplot as plt

# -------------------------
# Vehicle Parameters
# -------------------------
L = 1.53   # Wheelbase (m)

# Steering angle (degree)
theta_deg = np.linspace(10, 45, 500)

# Convert to radian
theta = np.deg2rad(theta_deg)

# Turning radius
R = L / np.tan(theta)

# -------------------------
# Plot
# -------------------------
plt.figure(figsize=(8,5))
plt.plot(theta_deg, R, linewidth=2)

plt.xlabel("Steering Angle (deg)")
plt.ylabel("Turning Radius R (m)")
plt.title("Theoretical Turning Radius\n$R=L/\\tan(\\theta)$")

plt.grid(True)
plt.xlim(0,45)
plt.ylim(0,np.max(R)*1.05)

plt.show()