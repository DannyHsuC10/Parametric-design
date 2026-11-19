import numpy as np
from scipy.optimize import fsolve

# ----------------------------
# Vehicle parameters
# ----------------------------
m = 320.0           # kg
mu = 1.84
g = 9.81
R = 18.25/2           # FSAE skidpad radius (m)

rho = 1.225
CL = 2.4
A = 1.2             # frontal area (m²)

# ----------------------------
# Solve maximum steady-state speed
# ----------------------------
def equation(v):
    downforce = 0.5 * rho * CL * A * v**2
    available_force = mu * (m * g + downforce)
    required_force = m * v**2 / R
    return available_force - required_force

v_max = fsolve(equation, 15.0)[0]

# ----------------------------
# Skidpad lap time
# ----------------------------
circumference = 2 * np.pi * R

time = circumference / v_max

ay = v_max**2 / R / g
downforce = 0.5 * rho * CL * A * v_max**2

print(f"Maximum Speed      : {v_max:.2f} m/s")
print(f"                   : {v_max*3.6:.2f} km/h")
print(f"Lateral Accel      : {ay:.2f} g")
print(f"Downforce          : {downforce:.1f} N")
print(f"Circle Length      : {circumference:.2f} m")
print(f"Theoretical Time   : {time:.3f} s")
