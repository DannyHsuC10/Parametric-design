import numpy as np
import matplotlib.pyplot as plt

# ==========================================================
# Vehicle Parameters
# ==========================================================

L = 1.53          # Wheelbase (m)
tf = 1.28         # Front Track (m)
tr = 1.25         # Rear Track (m)

# Front axle center turning radius
Rf = 9.125        # m

# ==========================================================
# Calculate Rear Axle Radius
# ==========================================================

Rr = np.sqrt(Rf**2 - L**2)

R_safe = Rf-0.1 - tf/2

# Wheel Path Radius
R_FI = Rf - tf/2
R_FO = Rf + tf/2

R_RI = Rr - tr/2
R_RO = Rr + tr/2

print("safe gap",R_safe-R_RI)
off_tracking = R_FI - R_RI

print(f"Rear axle radius : {Rr:.3f} m")
print(f"Front inner radius : {R_FI:.3f} m")
print(f"Rear inner radius : {R_RI:.3f} m")
print(f"Off Tracking : {off_tracking*1000:.1f} mm")

# ==========================================================
# Plot
# ==========================================================

theta = np.linspace(0, np.deg2rad(90), 300)

fig, ax = plt.subplots(figsize=(8,8))

# Front safe center
ax.plot(R_safe*np.cos(theta),
        R_safe*np.sin(theta),
        '--',
        color='gray',
        label='R_safe Center')

# Front axle center
ax.plot(Rf*np.cos(theta),
        Rf*np.sin(theta),
        '--',
        color='gray',
        label='Front Axle Center')

# Rear axle center
ax.plot(Rr*np.cos(theta),
        Rr*np.sin(theta),
        '--',
        color='black',
        label='Rear Axle Center')

# Front Inner
ax.plot(R_FI*np.cos(theta),
        R_FI*np.sin(theta),
        linewidth=3,
        label='Front Inner')


# Rear Inner
ax.plot(R_RI*np.cos(theta),
        R_RI*np.sin(theta),
        linewidth=3,
        label='Rear Inner')


# Front Outer
ax.plot(R_FO*np.cos(theta),
        R_FO*np.sin(theta),
        linewidth=3,
        label='Front Outer')

# Rear Outer
ax.plot(R_RO*np.cos(theta),
        R_RO*np.sin(theta),
        linewidth=3,
        label='Rear Outer')

# ==========================================================
# Draw Radius Lines
# ==========================================================

ax.plot([0, R_FI], [0, 0], '--')
ax.plot([0, R_RI], [0, 0], '--')

# ==========================================================
# Annotation
# ==========================================================

mid = (R_FI + R_RI)/2

ax.annotate("",
            xy=(R_FI,0.2),
            xytext=(R_RI,0.2),
            arrowprops=dict(arrowstyle="<->",lw=2))

ax.text(mid,
        0.35,
        f"Off Tracking = {off_tracking*1000:.0f} mm",
        ha='center')

# ==========================================================
# Figure Style
# ==========================================================

ax.set_aspect('equal')

margin = 0.5
ax.set_xlim(0, R_FO + margin)
ax.set_ylim(0, R_FO + margin)

ax.grid(True)
ax.legend()

ax.set_xlabel("X (m)")
ax.set_ylabel("Y (m)")
ax.set_title("Vehicle Swept Path Geometry")

plt.tight_layout()
plt.show()