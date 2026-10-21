# Heave：Ride rate 與自然頻率

## 分析目的

由 Damped_oscillation_analysis 後方延伸，分別計算前後軸解耦 heave 的彈簧剛度、輪端剛度、包含輪胎柔度的 ride rate、自然頻率與參考臨界阻尼。下一節點比較前後軸低／高速阻尼的 step 與頻率響應。

## 參數與方程式

前軸彈簧取自 Tire stiffness 的 Ks_pitch_N_per_m；後軸乘 hl_rear_heave_spring_ratio。MR 定義為彈簧／阻尼器位移除以該軸 heave 位移，Kt 是單輪輪胎剛度，軸上兩輪並聯。全車簧上質量依 hl_front_weight_ratio 分配，並沿用 ms。

$$
K_w=K_{spring}MR^2,\qquad K_{t,axle}=2K_t
$$

$$
K_{ride}=\frac{K_wK_{t,axle}}{K_w+K_{t,axle}},\qquad f_n=\frac{1}{2\pi}\sqrt{\frac{K_{ride}}{m_{s,axle}}}
$$

$$
c_{crit}=2\sqrt{K_wm_{s,axle}},\qquad c_{low/high}=\zeta_{avg,low/high}c_{crit}
$$

自然頻率是 ride rate 的簡化參考值；臨界阻尼以懸吊輪端剛度為參考，並不代表 2DOF 的兩個實際模態都有此阻尼比。低／高速平均阻尼比為該區域壓縮與回彈目標值的算術平均。

## 結果

主要圖表比較前後軸 ride rate 與自然頻率；heave_summary.csv 保留所有剛度、頻率及軸端阻尼係數，單位分別為 N/m、Hz 與 N s/m。
