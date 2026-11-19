"""
透過連續過彎路徑特徵路段優化前輪輪距
"""

import numpy as np

import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.patches import Arc

# ================================================(參數設定)
track_width = 10
offset_list = [
        0.01,
        0.16666666666666666,
        0.3333333333333333
    ]
r_cone = 0.16122034611053285
Driving_error = 0.2
# 預先計算
offsets = track_width * np.array(offset_list)
gap = 7  # 角錐間距
L = 1.53
d_lim = 190.5/2/1000 + r_cone + Driving_error  # 不包含輪距的半徑量(m)
best_wheel_track = 1.280
best_r_lim = (best_wheel_track / 2 + d_lim)
num_circles = 5

# ==============================================================(走線分析)

# Create 3 subplots side-by-side
fig, axs = plt.subplots(3, 1, figsize=(15, 5), constrained_layout=True)
for ax_idx, ax in enumerate(axs):
    # select offset index (0,1,2)
    try:
        this_offset = offsets[ax_idx]
    except Exception:
        this_offset = offsets[-1]

    # compute curve radius for this offset
    Curve_radius = ((gap / 2) ** 2 + (this_offset + best_r_lim) ** 2) / (2 * (this_offset + best_r_lim))

    print("最佳過彎半徑:",Curve_radius)

    offset_theta = np.rad2deg(np.arctan((2 * (Curve_radius - this_offset - best_r_lim)) / (gap)))

    # Draw circles and arcs for this subplot
    for i in range(num_circles):
        off = this_offset * ((-1) ** i)  # alternate sign for left/right cones
        x = i * gap
        y = off

        circle = Circle((x, y), best_r_lim, edgecolor='blue', facecolor='none', linewidth=2)
        ax.add_patch(circle)

        # determine arc angles depending on sign
        if off < 0:
            theta1 = 180 + offset_theta
            theta2 = 0 - offset_theta
        else:
            theta1 = 0 + offset_theta
            theta2 = 180 - offset_theta

        arc_center_y = off + (best_r_lim - Curve_radius) * np.sign(off)
        arc = Arc((x, arc_center_y), width=Curve_radius * 2, height=Curve_radius * 2,
                  theta1=theta1, theta2=theta2, linewidth=2)
        ax.add_patch(arc)

    # subplot settings
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title(f'slalom (offset index={offsets[ax_idx]})')
    ax.grid(True)
    ax.autoscale()
    ax.set_xlim(-gap, gap*num_circles+1)
    ax.set_aspect('equal')

plt.show()
