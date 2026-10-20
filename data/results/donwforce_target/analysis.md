# Donwforce_Target 分析

## 分析目的

掃描下壓力增加時，車輛可達的最大橫向加速度，並以無空力下壓力的狀況作為基準，解出skidpad 的目標情況。

## 輸入參數

- `ms`：四輪簧上質量總和（kg）。
- `mu`：單輪簧下質量（kg）。
- `mu_w`：輪胎與地面的摩擦係數。
- `skidpad_target_downforce_N`：由前序 `skidpad_test` 自動帶入，不需在此輸入。
- `skidpad_target_lap_time_s`：由前序 `skidpad_test` 自動帶入，不需在此輸入；目標秒數只需在 `skidpad_test` 設定。

車輛總質量以 $m=ms+4\mu$ 計算，重力加速度取 $g=9.81$ m/s$^2$。分析將下壓力由 0 掃描至 2500 N。

## 計算方式

依摩擦力上限與車重加下壓力計算橫向加速度，並轉換成重力加速度倍數：

$$
a_y=\mu_w\frac{mg+F_{down}}{m},\qquad
\frac{a_y}{g}=\mu_w\frac{mg+F_{down}}{mg}
$$

圖中的紅色標記為無下壓力基準；橘色星號標示 skidpad 目標圈速所需下壓力對應的最大橫向加速度。該點依下式計算：

$$
a_{y,target}=\mu_w\frac{mg+F_{target}}{m},\qquad
a_{y,target,g}=\frac{a_{y,target}}{g}
$$

圖上標註目標圈速、下壓力及實際最大橫向加速度。輸出 `downforce_target_actual_lateral_acceleration_m_per_s2` 為 m/s$^2$，`downforce_target_actual_lateral_acceleration_g` 為 g；`downforce_target_max_lateral_acceleration_g` 則是 2500 N 下壓力端點的加速度（g）。
