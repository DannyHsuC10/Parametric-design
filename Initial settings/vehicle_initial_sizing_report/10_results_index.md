# 完整結果索引

[返回主報告](README.md) · [上一篇：Roll 與 Pitch gradient](09_roll_pitch_gradients.md)

## 20. 完整結果索引

以下逐欄列出同次計算保存的完整結果。None 以「無可用解」顯示，布林狀態與負輪載均保留；各欄位的單位沿用名稱後綴及前文定義。

### cg

| 結果欄位 | 本次數值／狀態 |
| --- | --- |
| cg_min_track_m | 1.24 |
| cg_height_limit_45_m | 0.62 |
| cg_height_margin_45_m | 0.32 |
| cg_safe_45 | 是 |
| cg_status_45 | 通過幾何檢查 |
| cg_height_limit_60_m | 0.357957166898 |
| cg_height_margin_60_m | 0.0579571668976 |
| cg_safe_60 | 是 |
| cg_status_60 | 通過幾何檢查 |
| cg_geometric_safe | 是 |

### skidpad

| 結果欄位 | 本次數值／狀態 |
| --- | --- |
| F_ref | 414.616147129 |
| v_ref | 41.2805274682 |
| skidpad_target_lap_time_s | 5 |
| skidpad_target_downforce_N | 414.616147129 |
| skidpad_target_required_mu | 2.05641910253 |
| skidpad_total_mass_kg | 318.15 |
| skidpad_diameter_m | 18.25 |
| skidpad_safety_factor | 1.4 |
| skidpad_target_speed_m_per_s | 11.4668131856 |
| skidpad_target_lateral_acceleration_m_per_s2 | 14.4096224256 |
| skidpad_required_aero_downforce_N | 414.616147129 |

### aero

| 結果欄位 | 本次數值／狀態 |
| --- | --- |
| target_coefficient_C | 2.57409545977 |
| standard_downforce_coefficient_Cl | 5.14819091953 |

### angle_stiffness

| 結果欄位 | 本次數值／狀態 |
| --- | --- |
| pitch.stiffness_N_per_m | 75072.5385644 |
| pitch.displacement_m | 0.0133517687778 |
| roll.stiffness_N_per_m | 61859.5315449 |
| roll.displacement_m | 0.0218166156499 |

### compressed_travel

| 結果欄位 | 本次數值／狀態 |
| --- | --- |
| pitch.stiffness_N_per_m | 40094.0470588 |
| pitch.angle_deg | 1.87174496529 |
| roll.stiffness_N_per_m | 53982.62496 |
| roll.angle_deg | 2.29061004264 |

### selected_stiffness

| 結果欄位 | 本次數值／狀態 |
| --- | --- |
| pitch.stiffness_N_per_m | 75072.5385644 |
| pitch.frequency_Hz | 3.82058742194 |
| roll.stiffness_N_per_m | 61859.5315449 |
| roll.frequency_Hz | 3.46811032219 |

### tire

| 結果欄位 | 本次數值／狀態 |
| --- | --- |
| Ks | 59829.9149575 |
| Ks_pitch_N_per_m | 141433.712574 |
| Ks_roll_N_per_m | 100850.599177 |
| target_ride_rate_N_per_m | 34233.0175273 |
| actual_ride_rate_N_per_m | 34230.1087579 |

### frequency_mass

| 結果欄位 | 本次數值／狀態 |
| --- | --- |
| m_total_vehicle_kg | 318.15 |
| quarter_sprung_mass_kg | 65.1375 |
| unsprung_mass_ratio_target_percent | 18.1046676096 |
| equivalent_spring_stiffness_N_per_m | 60571.0779376 |
| wheel_rate_N_per_m | 60571.0779376 |
| ride_rate_N_per_m | 34471.4311514 |
| frequency_sprung_target_Hz | 3.66129098065 |
| frequency_unsprung_target_Hz | 15.7248630992 |

### heave

| 結果欄位 | 本次數值／狀態 |
| --- | --- |
| target_natural_frequency_Hz | 3.14497261984 |
| current_sprung_frequency_Hz | 3.66129098065 |
| current_unsprung_frequency_Hz | 15.7248630992 |
| can_reach_target | 是 |
| Ks_required_target_frequency_N_per_m | 48311.0003349 |
| Ks_scale_target_frequency | 0.341580514687 |
| heave_stiffness_reduction_N_per_m | 93122.7122387 |
| heave_stiffness_reduction_percent | 65.8419485313 |
| adjusted_sprung_frequency_Hz | 3.14497261984 |
| adjusted_unsprung_frequency_Hz | 14.3638254547 |

### tender

| 結果欄位 | 本次數值／狀態 |
| --- | --- |
| K_heave_main_N_per_m | 141433.712574 |
| K_tender_required_N_per_m | 73374.1959534 |
| tender_to_heave_stiffness_ratio | 0.518788587376 |
| K_series_target_N_per_m | 48311.0003349 |
| K_heave_with_tender_N_per_m | 48311.0003349 |

### anti_dive

| 結果欄位 | 本次數值／狀態 |
| --- | --- |
| anti_dive | 0.0909090909091 |
| anti_dive_percent | 9.09090909091 |
| anti_dive_suspension_fraction | 0.909090909091 |
| anti_dive_normalized_min_stiffness | 0.909090909091 |

### anti_scrub

| 結果欄位 | 本次數值／狀態 |
| --- | --- |
| anti_scrub | 0.0545454545455 |
| anti_scrub_percent | 5.45454545455 |

### front_rc

| 結果欄位 | 本次數值／狀態 |
| --- | --- |
| rc_normalized_optimal_ratio | 0.0909090909091 |
| rc_normalized_min_stiffness | 0.909090909091 |
| rc_suspension_fraction | 0.909090909091 |
| rc_normalized_optimal_height_m | 0.0272727272727 |

### rear_rc_height_m

| 結果欄位 | 本次數值／狀態 |
| --- | --- |
|  | 0.0330666666667 |

### fvsa

| 結果欄位 | 本次數值／狀態 |
| --- | --- |
| 前軸.max_roll_angle_rad | 0.0399786871233 |
| 前軸.max_roll_angle_deg | 2.29061004264 |
| 前軸.fvsa_length_m | 0.972043272039 |
| 前軸.fvsa_length_mm | 972.043272039 |
| 前軸.camber_change_rad_per_m | 0.799573742466 |
| 前軸.camber_gain_deg_per_m | 45.8122008528 |
| 前軸.camber_gain_deg_per_mm | 0.0458122008528 |
| 前軸.max_camber_change_deg | 1.14530502132 |
| 後軸.max_roll_angle_rad | 0.0403007483038 |
| 後軸.max_roll_angle_deg | 2.30906278903 |
| 後軸.fvsa_length_m | 0.959593717895 |
| 後軸.fvsa_length_mm | 959.593717895 |
| 後軸.camber_change_rad_per_m | 0.806014966076 |
| 後軸.camber_gain_deg_per_m | 46.1812557805 |
| 後軸.camber_gain_deg_per_mm | 0.0461812557805 |
| 後軸.max_camber_change_deg | 1.15453139451 |

### lateral_tire_roll

| 結果欄位 | 本次數值／狀態 |
| --- | --- |
| 前軸.axle_mass_kg | 159.075 |
| 前軸.lateral_force_N | 3433.15665 |
| 前軸.roll_moment_Nm | 1029.946995 |
| 前軸.axle_weight_N | 1560.52575 |
| 前軸.left_normal_load_N | -43.694721 |
| 前軸.right_normal_load_N | 1604.220471 |
| 前軸.normal_load_difference_N | 1647.915192 |
| 前軸.lateral_load_transfer_N | 823.957596 |
| 前軸.static_compression_m | 0.0097532859375 |
| 前軸.left_linear_compression_m | -0.0005461840125 |
| 前軸.right_linear_compression_m | 0.0200527558875 |
| 前軸.left_compression_change_m | -0.01029946995 |
| 前軸.right_compression_change_m | 0.01029946995 |
| 前軸.deformation_difference_m | 0.0205989399 |
| 前軸.linear_tire_roll_angle_rad | 0.01647915192 |
| 前軸.linear_tire_roll_angle_deg | 0.944185854971 |
| 前軸.tire_roll_angle_rad | —（無可用解） |
| 前軸.tire_roll_angle_deg | —（無可用解） |
| 前軸.contact_valid | 否 |
| 前軸.at_lift_boundary | 否 |
| 前軸.ay_contact_limit_g | 2.08333333333 |
| 後軸.axle_mass_kg | 159.075 |
| 後軸.lateral_force_N | 3433.15665 |
| 後軸.roll_moment_Nm | 1029.946995 |
| 後軸.axle_weight_N | 1560.52575 |
| 後軸.left_normal_load_N | -50.3395403226 |
| 後軸.right_normal_load_N | 1610.86529032 |
| 後軸.normal_load_difference_N | 1661.20483065 |
| 後軸.lateral_load_transfer_N | 830.602415323 |
| 後軸.static_compression_m | 0.0097532859375 |
| 後軸.left_linear_compression_m | -0.000629244254032 |
| 後軸.right_linear_compression_m | 0.020135816129 |
| 後軸.left_compression_change_m | -0.0103825301915 |
| 後軸.right_compression_change_m | 0.0103825301915 |
| 後軸.deformation_difference_m | 0.0207650603831 |
| 後軸.linear_tire_roll_angle_rad | 0.016746016438 |
| 後軸.linear_tire_roll_angle_deg | 0.959476065552 |
| 後軸.tire_roll_angle_rad | —（無可用解） |
| 後軸.tire_roll_angle_deg | —（無可用解） |
| 後軸.contact_valid | 否 |
| 後軸.at_lift_boundary | 否 |
| 後軸.ay_contact_limit_g | 2.06666666667 |

### caster

| 結果欄位 | 本次數值／狀態 |
| --- | --- |
| base_camber_deg | 2.08949087629 |
| steering_angle_deg | 27.0215815912 |
| kpi_deg | 8 |
| kpi_camber_change_deg | -0.870481487754 |
| required_caster_sine | 0.109541047923 |
| solution_status | solved |
| has_real_solution | 是 |
| caster_deg | 6.28885967803 |
| raw_steering_camber_change_deg | 2.08949087629 |
| camber_direction_factor | -1 |
| caster_camber_change_deg | 2.95997236404 |
| steering_camber_change_deg | -2.08949087629 |
| final_camber_deg | 0 |
| reason |  |

### steering_checks

| 結果欄位 | 本次數值／狀態 |
| --- | --- |
| [0].steering_angle_deg | 27.0215815912 |
| [0].raw_camber_change_deg | 3.82176691323 |
| [1].steering_angle_deg | -27.0215815912 |
| [1].raw_camber_change_deg | -5.56272988874 |

### compression

| 結果欄位 | 本次數值／狀態 |
| --- | --- |
| tender_bind_vehicle_downforce_N | 414.616147129 |
| tender_bind_force_N | 207.308073565 |
| main_spring_compression_mm | 1.4657613789 |
| tender_bind_spring_stroke_mm | 2.82535393909 |
| tender_bind_total_stroke_mm | 4.29111531799 |
| front_compression_mm | 4.29111531799 |
| rear_compression_mm | 4.29111531799 |
| heave_mm | 4.29111531799 |

### wheel_loads

| 結果欄位 | 本次數值／狀態 |
| --- | --- |
| total_mass_kg | 318.15 |
| total_normal_load_N | 3535.66764713 |
| front_axle_load_N | 543.892058859 |
| rear_axle_load_N | 2991.77558827 |
| longitudinal_transfer_N | 1223.94176471 |
| front_roll_fraction | 0.553972648658 |
| front_lateral_transfer_N | 912.899943676 |
| rear_lateral_transfer_N | 740.942790649 |
| wheel_loads_N.FL | -640.953914247 |
| wheel_loads_N.FR | 1184.84597311 |
| wheel_loads_N.RL | 754.945003486 |
| wheel_loads_N.RR | 2236.83058478 |
| contact_valid | 否 |

### tire_forces

| 結果欄位 | 本次數值／狀態 |
| --- | --- |
| wheel_forces.FL.raw_Fz_N | -640.953914247 |
| wheel_forces.FL.Fx_N | 0 |
| wheel_forces.FL.Fy_N | 0 |
| wheel_forces.FL.Fz_N | 0 |
| wheel_forces.FL.force_magnitude_N | 0 |
| wheel_forces.FL.load_fraction | 0 |
| wheel_forces.FR.raw_Fz_N | 1184.84597311 |
| wheel_forces.FR.Fx_N | 1770.79261182 |
| wheel_forces.FR.Fy_N | 1947.871873 |
| wheel_forces.FR.Fz_N | 1184.84597311 |
| wheel_forces.FR.force_magnitude_N | 2886.82720087 |
| wheel_forces.FR.load_fraction | 0.283685259891 |
| wheel_forces.RL.raw_Fz_N | 754.945003486 |
| wheel_forces.RL.Fx_N | 1128.29098874 |
| wheel_forces.RL.Fy_N | 1241.12008762 |
| wheel_forces.RL.Fz_N | 754.945003486 |
| wheel_forces.RL.force_magnitude_N | 1839.39163461 |
| wheel_forces.RL.load_fraction | 0.180754945688 |
| wheel_forces.RR.raw_Fz_N | 2236.83058478 |
| wheel_forces.RR.Fx_N | 3343.01939943 |
| wheel_forces.RR.Fy_N | 3677.32133938 |
| wheel_forces.RR.Fz_N | 2236.83058478 |
| wheel_forces.RR.force_magnitude_N | 5449.94330274 |
| wheel_forces.RR.load_fraction | 0.535559794421 |
| total_Fx_N | 6242.103 |
| total_Fy_N | 6866.3133 |
| clipped_total_Fz_N | 4176.62156138 |
| contact_valid | 否 |
| reference_only | 是 |
| most_loaded_wheel | RR |

### gear

| 結果欄位 | 本次數值／狀態 |
| --- | --- |
| total_mass_kg | 318.15 |
| gear_rate_acceleration_g | 1.2 |
| gear_rate_target_speed_kmh | 110 |
| front_axle_load_N | 826.160691176 |
| rear_axle_load_N | 2294.89080882 |
| longitudinal_transfer_N | 734.365058824 |
| total_Fx_N | 3745.2618 |
| front_axle_Fx_N | 991.392829412 |
| rear_axle_Fx_N | 2753.86897059 |
| maximum_wheel_Fx_N | 1376.93448529 |
| wheel_torque_required_Nm | 275.386897059 |
| target_wheel_rpm | 1458.92031168 |
| gear_ratio_accel | 12.3460587654 |
| gear_ratio_top_speed | 10.2815759572 |
| gear_ratio_avg | 11.3138173613 |

### brake

| 結果欄位 | 本次數值／狀態 |
| --- | --- |
| total_mass_kg | 318.15 |
| requested_point.deceleration_g | 2 |
| requested_point.front_axle_load_N | 2784.46751471 |
| requested_point.rear_axle_load_N | 336.583985294 |
| requested_point.longitudinal_transfer_N | 1223.94176471 |
| requested_point.front_brake_force_N | 5568.93502941 |
| requested_point.rear_brake_force_N | 673.167970588 |
| requested_point.front_ratio | 0.892156862745 |
| requested_point.rear_ratio | 0.107843137255 |
| limit_point.deceleration_g | 1.60465645757 |
| limit_point.front_axle_load_N | 2542.52877821 |
| limit_point.rear_axle_load_N | 578.52272179 |
| limit_point.longitudinal_transfer_N | 982.00302821 |
| limit_point.front_brake_force_N | 4079.8852225 |
| limit_point.rear_brake_force_N | 928.330221369 |
| limit_point.front_ratio | 0.814638521091 |
| limit_point.rear_ratio | 0.185361478909 |
| samples[0].deceleration_g | 0.1 |
| samples[0].front_axle_load_N | 1621.72283824 |
| samples[0].rear_axle_load_N | 1499.32866176 |
| samples[0].longitudinal_transfer_N | 61.1970882353 |
| samples[0].front_brake_force_N | 162.172283824 |
| samples[0].rear_brake_force_N | 149.932866176 |
| samples[0].front_ratio | 0.519607843137 |
| samples[0].rear_ratio | 0.480392156863 |
| samples[1].deceleration_g | 0.267184050841 |
| samples[1].front_axle_load_N | 1724.03460934 |
| samples[1].rear_axle_load_N | 1397.01689066 |
| samples[1].longitudinal_transfer_N | 163.508859344 |
| samples[1].front_brake_force_N | 460.634550714 |
| samples[1].rear_brake_force_N | 373.260631938 |
| samples[1].front_ratio | 0.552389029577 |
| samples[1].rear_ratio | 0.447610970423 |
| samples[2].deceleration_g | 0.434368101681 |
| samples[2].front_axle_load_N | 1826.34638045 |
| samples[2].rear_axle_load_N | 1294.70511955 |
| samples[2].longitudinal_transfer_N | 265.820630452 |
| samples[2].front_brake_force_N | 793.30661029 |
| samples[2].rear_brake_force_N | 562.378605015 |
| samples[2].front_ratio | 0.585170216016 |
| samples[2].rear_ratio | 0.414829783984 |
| samples[3].deceleration_g | 0.601552152522 |
| samples[3].front_axle_load_N | 1928.65815156 |
| samples[3].rear_axle_load_N | 1192.39334844 |
| samples[3].longitudinal_transfer_N | 368.13240156 |
| samples[3].front_brake_force_N | 1160.18846255 |
| samples[3].rear_brake_force_N | 717.286785407 |
| samples[3].front_ratio | 0.617951402455 |
| samples[3].rear_ratio | 0.382048597545 |
| samples[4].deceleration_g | 0.768736203363 |
| samples[4].front_axle_load_N | 2030.96992267 |
| samples[4].rear_axle_load_N | 1090.08157733 |
| samples[4].longitudinal_transfer_N | 470.444172669 |
| samples[4].front_brake_force_N | 1561.2801075 |
| samples[4].rear_brake_force_N | 837.985173113 |
| samples[4].front_ratio | 0.650732588895 |
| samples[4].rear_ratio | 0.349267411105 |
| samples[5].deceleration_g | 0.935920254204 |
| samples[5].front_axle_load_N | 2133.28169378 |
| samples[5].rear_axle_load_N | 987.769806223 |
| samples[5].longitudinal_transfer_N | 572.755943777 |
| samples[5].front_brake_force_N | 1996.58154513 |
| samples[5].rear_brake_force_N | 924.473768135 |
| samples[5].front_ratio | 0.683513775334 |
| samples[5].rear_ratio | 0.316486224666 |
| samples[6].deceleration_g | 1.10310430504 |
| samples[6].front_axle_load_N | 2235.59346489 |
| samples[6].rear_axle_load_N | 885.458035115 |
| samples[6].longitudinal_transfer_N | 675.067714885 |
| samples[6].front_brake_force_N | 2466.09277544 |
| samples[6].rear_brake_force_N | 976.752570471 |
| samples[6].front_ratio | 0.716294961773 |
| samples[6].rear_ratio | 0.283705038227 |
| samples[7].deceleration_g | 1.27028835588 |
| samples[7].front_axle_load_N | 2337.90523599 |
| samples[7].rear_axle_load_N | 783.146264006 |
| samples[7].longitudinal_transfer_N | 777.379485994 |
| samples[7].front_brake_force_N | 2969.81379845 |
| samples[7].rear_brake_force_N | 994.821580122 |
| samples[7].front_ratio | 0.749076148213 |
| samples[7].rear_ratio | 0.250923851787 |
| samples[8].deceleration_g | 1.43747240673 |
| samples[8].front_axle_load_N | 2440.2170071 |
| samples[8].rear_axle_load_N | 680.834492898 |
| samples[8].longitudinal_transfer_N | 879.691257102 |
| samples[8].front_brake_force_N | 3507.74461413 |
| samples[8].rear_brake_force_N | 978.680797088 |
| samples[8].front_ratio | 0.781857334652 |
| samples[8].rear_ratio | 0.218142665348 |
| samples[9].deceleration_g | 1.60465645757 |
| samples[9].front_axle_load_N | 2542.52877821 |
| samples[9].rear_axle_load_N | 578.52272179 |
| samples[9].longitudinal_transfer_N | 982.00302821 |
| samples[9].front_brake_force_N | 4079.8852225 |
| samples[9].rear_brake_force_N | 928.330221369 |
| samples[9].front_ratio | 0.814638521091 |
| samples[9].rear_ratio | 0.185361478909 |
| required_tire_mu | 2 |
| rear_lift_limit_g | 2.55 |
| physical_deceleration_limit_g | 1.60465645757 |
| target_achievable | 否 |
| brake_design_deceleration_g | 1.60465645757 |
| brake_ideal_front_ratio | 0.753055637136 |
| brake_ideal_rear_ratio | 0.246944362864 |
| brake_ideal_fit_rear_over_front | 0.327923131687 |

### brake_mechanical_advantage

| 結果欄位 | 本次數值／狀態 |
| --- | --- |
| brake_total_required_force_N | 6242.103 |
| brake_driver_force_N | 500 |
| brake_mechanical_advantage | 12.484206 |

### damping

| 結果欄位 | 本次數值／狀態 |
| --- | --- |
| roll_total_stiffness_Nm_per_rad | 284452.782273 |
| roll_total_critical_damping_Nms_per_rad | 3001.49692071 |
| roll.front.spring_stiffness_N_per_m | 100850.599177 |
| roll.front.angular_stiffness_Nm_per_rad | 157579.061214 |
| roll.front.stiffness_fraction | 0.553972648658 |
| roll.front.angular_damping_Nms_per_rad | 1662.7471991 |
| roll.front.damper_critical_damping_Ns_per_m | 1064.15820743 |
| roll.rear.spring_stiffness_N_per_m | 82514.1265992 |
| roll.rear.angular_stiffness_Nm_per_rad | 126873.721059 |
| roll.rear.stiffness_fraction | 0.446027351342 |
| roll.rear.angular_damping_Nms_per_rad | 1338.74972161 |
| roll.rear.damper_critical_damping_Ns_per_m | 870.674896986 |
| heave_with_tender.front.sprung_mass_kg | 130.275 |
| heave_with_tender.front.spring_stiffness_N_per_m | 48311.0003349 |
| heave_with_tender.front.body_stiffness_N_per_m | 48311.0003349 |
| heave_with_tender.front.body_critical_damping_Ns_per_m | 5017.45575711 |
| heave_with_tender.front.damper_critical_damping_Ns_per_m | 5017.45575711 |
| heave_with_tender.rear.sprung_mass_kg | 130.275 |
| heave_with_tender.rear.spring_stiffness_N_per_m | 48311.0003349 |
| heave_with_tender.rear.body_stiffness_N_per_m | 48311.0003349 |
| heave_with_tender.rear.body_critical_damping_Ns_per_m | 5017.45575711 |
| heave_with_tender.rear.damper_critical_damping_Ns_per_m | 5017.45575711 |
| pure_heave.front.sprung_mass_kg | 130.275 |
| pure_heave.front.spring_stiffness_N_per_m | 141433.712574 |
| pure_heave.front.body_stiffness_N_per_m | 141433.712574 |
| pure_heave.front.body_critical_damping_Ns_per_m | 8584.93492242 |
| pure_heave.front.damper_critical_damping_Ns_per_m | 8584.93492242 |
| pure_heave.rear.sprung_mass_kg | 130.275 |
| pure_heave.rear.spring_stiffness_N_per_m | 141433.712574 |
| pure_heave.rear.body_stiffness_N_per_m | 141433.712574 |
| pure_heave.rear.body_critical_damping_Ns_per_m | 8584.93492242 |
| pure_heave.rear.damper_critical_damping_Ns_per_m | 8584.93492242 |

### rate_cases

| 結果欄位 | 本次數值／狀態 |
| --- | --- |
| front.combined_average.spring_rate_N_per_m | 74580.7997559 |
| front.combined_average.wheel_rate_N_per_m | 74580.7997559 |
| front.combined_average.ride_rate_N_per_m | 38597.7041773 |
| front.combined_average.sprung_mass_per_wheel_kg | 65.1375 |
| front.combined_average.spring_coordinate_mass_kg | 65.1375 |
| front.combined_average.frequency_Ks_Hz | 5.38540174371 |
| front.combined_average.frequency_Kw_Hz | 5.38540174371 |
| front.combined_average.frequency_Kr_Hz | 3.87422933478 |
| front.combined_average.critical_damping_Ks_Ns_per_m | 4408.17733042 |
| front.combined_average.critical_damping_Kw_Ns_per_m | 4408.17733042 |
| front.combined_average.critical_damping_Kr_Ns_per_m | 3171.21929601 |
| front.heave_with_tender.spring_rate_N_per_m | 48311.0003349 |
| front.heave_with_tender.wheel_rate_N_per_m | 48311.0003349 |
| front.heave_with_tender.ride_rate_N_per_m | 30121.1900516 |
| front.heave_with_tender.sprung_mass_per_wheel_kg | 65.1375 |
| front.heave_with_tender.spring_coordinate_mass_kg | 65.1375 |
| front.heave_with_tender.frequency_Ks_Hz | 4.33438618664 |
| front.heave_with_tender.frequency_Kw_Hz | 4.33438618664 |
| front.heave_with_tender.frequency_Kr_Hz | 3.42247789425 |
| front.heave_with_tender.critical_damping_Ks_Ns_per_m | 3547.87699015 |
| front.heave_with_tender.critical_damping_Kw_Ns_per_m | 3547.87699015 |
| front.heave_with_tender.critical_damping_Kr_Ns_per_m | 2801.44178378 |
| front.roll.spring_rate_N_per_m | 100850.599177 |
| front.roll.wheel_rate_N_per_m | 100850.599177 |
| front.roll.ride_rate_N_per_m | 44611.6737841 |
| front.roll.sprung_mass_per_wheel_kg | 65.1375 |
| front.roll.spring_coordinate_mass_kg | 65.1375 |
| front.roll.frequency_Ks_Hz | 6.26244363386 |
| front.roll.frequency_Kw_Hz | 6.26244363386 |
| front.roll.frequency_Kr_Hz | 4.16513274797 |
| front.roll.critical_damping_Ks_Ns_per_m | 5126.07292335 |
| front.roll.critical_damping_Kw_Ns_per_m | 5126.07292335 |
| front.roll.critical_damping_Kr_Ns_per_m | 3409.33594773 |
| front.heave_only.spring_rate_N_per_m | 141433.712574 |
| front.heave_only.wheel_rate_N_per_m | 141433.712574 |
| front.heave_only.ride_rate_N_per_m | 51097.4452552 |
| front.heave_only.sprung_mass_per_wheel_kg | 65.1375 |
| front.heave_only.spring_coordinate_mass_kg | 65.1375 |
| front.heave_only.frequency_Ks_Hz | 7.41619361332 |
| front.heave_only.frequency_Kw_Hz | 7.41619361332 |
| front.heave_only.frequency_Kr_Hz | 4.45763168847 |
| front.heave_only.critical_damping_Ks_Ns_per_m | 6070.46569969 |
| front.heave_only.critical_damping_Kw_Ns_per_m | 6070.46569969 |
| front.heave_only.critical_damping_Kr_Ns_per_m | 3648.75860551 |
| rear.combined_average.spring_rate_N_per_m | 65412.5634671 |
| rear.combined_average.wheel_rate_N_per_m | 65412.5634671 |
| rear.combined_average.ride_rate_N_per_m | 35987.2967823 |
| rear.combined_average.sprung_mass_per_wheel_kg | 65.1375 |
| rear.combined_average.spring_coordinate_mass_kg | 65.1375 |
| rear.combined_average.frequency_Ks_Hz | 5.04353655759 |
| rear.combined_average.frequency_Kw_Hz | 5.04353655759 |
| rear.combined_average.frequency_Kr_Hz | 3.74092672242 |
| rear.combined_average.critical_damping_Ks_Ns_per_m | 4128.3463289 |
| rear.combined_average.critical_damping_Kw_Ns_per_m | 4128.3463289 |
| rear.combined_average.critical_damping_Kr_Ns_per_m | 3062.10551363 |
| rear.heave_with_tender.spring_rate_N_per_m | 48311.0003349 |
| rear.heave_with_tender.wheel_rate_N_per_m | 48311.0003349 |
| rear.heave_with_tender.ride_rate_N_per_m | 30121.1900516 |
| rear.heave_with_tender.sprung_mass_per_wheel_kg | 65.1375 |
| rear.heave_with_tender.spring_coordinate_mass_kg | 65.1375 |
| rear.heave_with_tender.frequency_Ks_Hz | 4.33438618664 |
| rear.heave_with_tender.frequency_Kw_Hz | 4.33438618664 |
| rear.heave_with_tender.frequency_Kr_Hz | 3.42247789425 |
| rear.heave_with_tender.critical_damping_Ks_Ns_per_m | 3547.87699015 |
| rear.heave_with_tender.critical_damping_Kw_Ns_per_m | 3547.87699015 |
| rear.heave_with_tender.critical_damping_Kr_Ns_per_m | 2801.44178378 |
| rear.roll.spring_rate_N_per_m | 82514.1265992 |
| rear.roll.wheel_rate_N_per_m | 82514.1265992 |
| rear.roll.ride_rate_N_per_m | 40618.8081373 |
| rear.roll.sprung_mass_per_wheel_kg | 65.1375 |
| rear.roll.spring_coordinate_mass_kg | 65.1375 |
| rear.roll.frequency_Ks_Hz | 5.66459340116 |
| rear.roll.frequency_Kw_Hz | 5.66459340116 |
| rear.roll.frequency_Kr_Hz | 3.97436890689 |
| rear.roll.critical_damping_Ks_Ns_per_m | 4636.70741857 |
| rear.roll.critical_damping_Kw_Ns_per_m | 4636.70741857 |
| rear.roll.critical_damping_Kr_Ns_per_m | 3253.18773823 |
| rear.heave_only.spring_rate_N_per_m | 141433.712574 |
| rear.heave_only.wheel_rate_N_per_m | 141433.712574 |
| rear.heave_only.ride_rate_N_per_m | 51097.4452552 |
| rear.heave_only.sprung_mass_per_wheel_kg | 65.1375 |
| rear.heave_only.spring_coordinate_mass_kg | 65.1375 |
| rear.heave_only.frequency_Ks_Hz | 7.41619361332 |
| rear.heave_only.frequency_Kw_Hz | 7.41619361332 |
| rear.heave_only.frequency_Kr_Hz | 4.45763168847 |
| rear.heave_only.critical_damping_Ks_Ns_per_m | 6070.46569969 |
| rear.heave_only.critical_damping_Kw_Ns_per_m | 6070.46569969 |
| rear.heave_only.critical_damping_Kr_Ns_per_m | 3648.75860551 |

### gradients

| 結果欄位 | 本次數值／狀態 |
| --- | --- |
| roll_axis_height_at_cg_m | 0.0301696969697 |
| roll_moment_arm_m | 0.26983030303 |
| roll_suspension_stiffness_Nm_per_rad | 284452.782273 |
| roll_ride_stiffness_Nm_per_rad | 86174.0736393 |
| roll_gradient_suspension_deg_per_g | 0.169630562584 |
| roll_gradient_with_tires_deg_per_g | 0.559935064547 |
| pitch.heave_with_tender.pitch_suspension_stiffness_Nm_per_rad | 56545.610342 |
| pitch.heave_with_tender.pitch_tire_stiffness_Nm_per_rad | 187272 |
| pitch.heave_with_tender.gradient_suspension_deg_per_g | 0.948737192037 |
| pitch.heave_with_tender.gradient_with_tires_deg_per_g | 1.23520245955 |
| pitch.heave_with_tender.gradient_with_tires_and_anti_dive_deg_per_g | 1.14895362391 |
| pitch.heave_only.pitch_suspension_stiffness_Nm_per_rad | 165541.088882 |
| pitch.heave_only.pitch_tire_stiffness_Nm_per_rad | 187272 |
| pitch.heave_only.gradient_suspension_deg_per_g | 0.324070138358 |
| pitch.heave_only.gradient_with_tires_deg_per_g | 0.610535405872 |
| pitch.heave_only.gradient_with_tires_and_anti_dive_deg_per_g | 0.581074484203 |

---

[返回主報告](README.md) · [上一篇：Roll 與 Pitch gradient](09_roll_pitch_gradients.md)
