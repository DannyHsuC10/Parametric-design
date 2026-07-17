"""
透過連續過彎路徑特徵路段優化前輪輪距
"""

from json_data import file_data
from pathlib import Path
from geometry_data import geometry_data
import numpy as np

import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.patches import Arc

# 設定物件
base_dir = Path(__file__).resolve().parent.parent
current_dir = Path(__file__).resolve().parent
figures_dir = current_dir / "Figures"
figures_dir.mkdir(exist_ok=True)
geometry = geometry_data()

data = file_data(base_dir/"track.json")# 導入摩擦係數使用
data.load_json(base_dir/"tire.json")
geometry.load_json(base_dir/"geometry.json")


print("track_Minimum_radius : ", data.track_Minimum_radius)# 賽道最小半徑估算
# ================================================(輪距最佳化)

wheel_track_values = np.arange(1200, 1400 + 1, 10) / 1000.0
max_steer_angles = []
r_best_matrix = []


# 預先計算
offsets = geometry.track_width * np.array(geometry.offset_list)
gap = geometry.gap_cones  # 角錐間距
L = geometry.L
d_lim = data.tire_width/2/1000 + geometry.r_cone + geometry.Driving_error  # 不包含輪距的半徑量(m)

for wheel_track in wheel_track_values:

    
    r_lim = (wheel_track / 2 + d_lim)  # 最小半徑量

    Curve_radius_list = []
    for this_offset in offsets:
        Curve_radius = ((gap / 2) ** 2 + (this_offset + r_lim) ** 2) / (2 * (this_offset + r_lim))
        Curve_radius_list.append(Curve_radius)

    r_best = np.array(Curve_radius_list)
    # print(r_best)# 檢查用
    r_best_matrix.append(r_best)

    # Ideal Ackermann steering
    delta_mid = np.rad2deg(np.arctan(L / r_best))
    delta_in = np.rad2deg(np.arctan(L / (r_best - wheel_track / 2)))
    delta_out = np.rad2deg(np.arctan(L / (r_best + wheel_track / 2)))

    max_steer_angles.append(float(np.max(np.vstack([delta_in, delta_out]))))

r_best_matrix = np.vstack(r_best_matrix)

plt.figure(figsize=(8, 5))
for offset_idx in range(r_best_matrix.shape[1]):
    plt.plot(wheel_track_values * 1000,
             r_best_matrix[:, offset_idx],
             marker='o',
             linestyle='-',
             label=f'offset index {offset_idx}')
plt.grid(True)
plt.xlabel('wheel_track (mm)')
plt.ylabel('r_best (m)')
plt.title('wheel_track vs. r_best')
plt.legend()
plt.tight_layout()
plt.savefig(figures_dir/"wheel_track_vs_r_best.png", dpi=300)


x = wheel_track_values * 1000
y = np.array(max_steer_angles)

dy = np.gradient(y, x)

dx = np.gradient(dy, x)

# Find turning points where derivative sign changes
sign_changes = np.where(np.sign(dy[:-1]) != np.sign(dy[1:]))[0] + 1
turn_points = [(x[idx], y[idx]) for idx in sign_changes]

# Find maximum second derivative point
max_ddx_idx = int(np.nanargmax(dx))
best_track = x[max_ddx_idx]
best_angle = y[max_ddx_idx]

# Compute best-track parameters again for printing
best_wheel_track = wheel_track_values[max_ddx_idx]
best_r_lim = (best_wheel_track / 2 + d_lim)
best_curve_radius_list = [((gap / 2) ** 2 + (this_offset + best_r_lim) ** 2) / (2 * (this_offset + best_r_lim)) for this_offset in offsets]
best_r_best = np.array(best_curve_radius_list)
best_delta_mid = np.rad2deg(np.arctan(L / best_r_best))
best_delta_in = np.rad2deg(np.arctan(L / (best_r_best - best_wheel_track / 2)))
best_delta_out = np.rad2deg(np.arctan(L / (best_r_best + best_wheel_track / 2)))

best_max_angle = float(np.max(np.vstack([best_delta_in, best_delta_out])))

plt.figure(figsize=(8, 5))
plt.plot(x, y, marker='o', linestyle='-')
if turn_points:
    tp_x = [p[0] for p in turn_points]
    tp_y = [p[1] for p in turn_points]
    plt.scatter(tp_x, tp_y, color='red', s=80, label='turning points')
plt.scatter([best_track], [best_angle], color='green', s=100, marker='*', label='best track (max 2nd derivative)')
plt.annotate(f'best track={best_track:.0f} mm', xy=(best_track, best_angle), xytext=(best_track+10, best_angle+0.2),
             arrowprops=dict(arrowstyle='->', color='green'))
plt.grid(True)
plt.xlabel('wheel_track (mm)')
plt.ylabel('max_wheel_steer_angles (deg)')
plt.title('wheel_track vs. max_steer_angles')
plt.legend()
plt.tight_layout()
plt.savefig(figures_dir/"wheel_track_vs_max_steer_angles.png", dpi=300)


plt.figure(figsize=(8, 5))
plt.plot(x, dx, marker='o', linestyle='-', label='second derivative')
plt.scatter([best_track], [dx[max_ddx_idx]], color='green', s=100, marker='*', label='max second derivative')
plt.axvline(best_track, color='green', linestyle='--', alpha=0.7)
plt.axhline(0, color='gray', linestyle='--')
plt.grid(True)
plt.xlabel('wheel_track (mm)')
plt.ylabel('Second derivative (deg/mm²)')
plt.title('Second derivative of max steer angle')
plt.legend()
plt.tight_layout()
plt.savefig(figures_dir/"second_derivative_of_max_steer_angle.png", dpi=300)

print("===========(理想阿克曼轉向)============")
print(f"Best wheel track : {best_track:.0f} mm")
print(f"Best max steering angle : {best_max_angle:.4f} deg")
print(f"Best r_best values : {best_r_best}")
print(f"Middle steering angle : {best_delta_mid} deg")
print(f"Inner steering angle : {best_delta_in} deg")
print(f"Outer steering angle : {best_delta_out} deg")
print(f"Ackermann difference : {best_delta_in - best_delta_out} deg")
print("最大角度: ", best_max_angle)



# ==============================================================(走線分析)
# 參數設定

num_circles = 5

# Prepare three offsets (use indices 0,1,2)
offsets = geometry.track_width * np.array(geometry.offset_list)
gap = geometry.gap_cones  # 角錐間距

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
plt.tight_layout()
plt.savefig(figures_dir/"slalom_three_offsets.png", dpi=300)

if geometry.show_plt:
    plt.show()
else:
    plt.close('all')
    


geometry.track_front = best_wheel_track
geometry.save_json(base_dir/"geometry.json")
