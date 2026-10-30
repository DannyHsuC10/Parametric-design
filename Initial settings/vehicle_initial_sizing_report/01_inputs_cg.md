# 輸入參數、質量與重心

[返回主報告](README.md) · [下一篇：Skidpad 與空力需求](02_skidpad_aero.md)

## 0. 本次輸入、質量與幾何

| 參數 | 本次值 | 單位／定義 |
| --- | --- | --- |
| use_tender | 是 | 是否使用 Tender 彈簧 |
| ms | 260.55 | kg（全車簧上） |
| mu | 14.4 | kg（單輪簧下） |
| h_cog | 0.3 | m |
| lf | 0.765 | m |
| lr | 0.765 | m |
| ax | 2 | g |
| ay | 2.2 | g |
| a_acc | 1.2 | g |
| brake_ax | 2 | g |
| target_lap_time_s | 5 | s |
| drive_target_speed_kmh | 110 | km/h |
| sus_travel | 0.025 | m |
| tf | 1.25 | m |
| tr | 1.24 | m |
| t | 1.25 | m |
| A_air | 1 | m² |
| air_density_kg_per_m3 | 1.225 | kg/m³ |
| kf | 0.55 | 比例／無因次 |
| kr | 0.45 | 比例／無因次 |
| target_pitch_angle_deg | 1 | deg |
| target_roll_angle_deg | 2 | deg |
| kpi_deg | 8 | deg |
| min_turn_radius_m | 3 | m |
| caster_direction_check_deg | 10 | deg |
| MR | 1 | 無因次 |
| sprung_roll_inertia_kg_m2 | 7.91782004473 | kg·m² |
| Kt | 80000 | N/m（單輪） |
| wl_mu_y | 1.81526957993 | 比例／無因次 |
| mu_w | 1.60465645757 | 比例／無因次 |
| R_tire | 0.2 | m |
| drive_motor_torque_Nm | 22.30565254 | N·m |
| drive_motor_rpm | 15000 | rpm |
| N | 5 | 比例／無因次 |
| rc_chassis_stiffness_ratio | 10 | 比例／無因次 |
| F_ref_ratio | 1 | 比例／無因次 |
| wl_aero_front_ratio | 0.5 | 比例／無因次 |
| cg_safety_factor | 1 | 比例／無因次 |
| brake_driver_force_N | 500 | N |
| g | 9.81 | m/s² |
| L | 1.53 | m |
| wf | 0.5 | 比例／無因次 |
| wr | 0.5 | 比例／無因次 |
| steering_angle_deg | 27.0215815912 | deg（由半徑導出） |
| active_heave_spring_N_per_m | 48311.0003349 | N/m（本次採用的 Heave 剛性） |

$$
L=l_f+l_r
$$

$$
L=0.765+0.765=1.53\ \mathrm{m}
$$

$$
w_f=\frac{l_r}{L},\quad w_r=\frac{l_f}{L}
$$

$$
w_f=\frac{0.765}{1.53}=0.5,\quad w_r=\frac{0.765}{1.53}=0.5
$$

$$
M=M_s+4m_u
$$

$$
M=260.55+4\cdot14.4=318.15\ \mathrm{kg}
$$

$$
m_{s,q}=\frac{M_s}{4}
$$

$$
m_{s,q}=\frac{260.55}{4}=65.1375\ \mathrm{kg}
$$

## 1. CG：重心高度與傾斜幾何檢查

$$
h_{\max}=\frac{\min(t_f,t_r)}{2S_F\tan\beta},\quad \mathrm{margin}=h_{\max}-h
$$

$$
\beta=45^\circ
$$

$$
h_{\max}=\frac{1.24}{2\cdot1\cdot\tan(0.785398163397)}=0.62\ \mathrm{m}
$$

$$
\mathrm{margin}=h_{\max}-h
$$

$$
\mathrm{margin}=0.62-0.3=0.32\ \mathrm{m}
$$

45° 判定：**通過幾何檢查**。

$$
\beta=60^\circ
$$

$$
h_{\max}=\frac{1.24}{2\cdot1\cdot\tan(1.0471975512)}=0.357957166898\ \mathrm{m}
$$

$$
\mathrm{margin}=h_{\max}-h
$$

$$
\mathrm{margin}=0.357957166898-0.3=0.0579571668976\ \mathrm{m}
$$

60° 判定：**通過幾何檢查**。

這是左右對稱、無懸吊變形的幾何檢查。

---

[返回主報告](README.md) · [下一篇：Skidpad 與空力需求](02_skidpad_aero.md)
