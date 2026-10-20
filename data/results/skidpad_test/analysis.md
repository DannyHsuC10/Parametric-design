# skidpad_test 分析

## 分析目的

依據目標 skidpad 圈速，估算車速、向心加速度、所需摩擦係數與所需下壓力。分析會把目標圈速所需的下壓力與車速輸出給下一步 `Aero CL CD`。

## 輸入參數

- `ms`：四輪簧上質量總和（kg）。
- `mu`：單輪簧下質量（kg）。
- `mu_w`：輪胎與地面的摩擦係數。
- `target_lap_time_s`：目標圈速（秒），需介於 4 至 6 秒；預設為 5.0 秒。只需在 `skidpad_test` 設定。

車輛總質量依 $m=ms+4\mu$ 計算。skidpad 直徑固定為 $D=18.25$ m，安全係數固定為 1.4。

## 計算方式

半徑及周長為：

$$
R=\frac{D}{2},\qquad L=\pi D
$$

圈速 $t$ 對應車速、向心加速度與需求摩擦係數：

$$
v=\frac{L}{t},\qquad a_y=\frac{v^2}{R},\qquad
\mu_{required}=1.4\frac{a_y}{g}
$$

依輪胎摩擦係數反推需求下壓力：

$$
F_{down}=\left(\frac{\mu_{required}}{\mu_w}-1\right)mg
$$

圖表中的紅色標記顯示固定參考圈速；橘色星號顯示輸入的目標圈速。目標圈速對應的下壓力會以 `skidpad_target_downforce_N` 輸出，並同時作為 `F_ref` 傳給下一個分析；目標車速以 km/h 作為 `v_ref` 傳遞。
