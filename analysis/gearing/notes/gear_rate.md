# Gear_rate：加速與極速齒比

使用手動設定的 `acc_g` 計算加速需求，$r_w$ 為輪胎半徑，$T_m$、$n_m$ 為馬達最大扭矩與轉速。

$T_m$ 自動使用 `motor` 分析曲線的 `max(torque)`，即 `drive_motor_torque_Nm`；$n_m$ 使用可編輯的 `drive_motor_rpm`。

$$a_t=\mathrm{acc\_g}\,g$$

$$N_r=mgw_f+\frac{ma_t h}{L},\qquad N_f=mg-N_r$$

$$F_f=ma_t\frac{N_f}{mg},\qquad F_r=ma_t\frac{N_r}{mg}$$

$$T_{w,req}=\frac{r_w}{2}\max(F_f,F_r),\qquad i_{acc}=\frac{T_{w,req}}{T_m}$$

目標車速 $V_t$ 使用 km/h，輪速 $n_w$ 使用 rpm：

$$n_w=\frac{V_t/3.6}{2\pi r_w}\,60,\qquad i_{speed}=\frac{n_m}{n_w}$$

$$i_{avg}=\frac{i_{acc}+i_{speed}}{2}$$

$i_{avg}$ 傳給齒數搜尋；上述加速齒比公式未乘傳動效率。$w_f$ 為輸入的前軸配重，載重式保留現行程式將其用於後軸靜態項的配置。
