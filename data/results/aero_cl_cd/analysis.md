# Aero CL CD 分析

## 分析目的

使用前一步 `skidpad_test` 在與下壓力目標目標圈速下計算的下壓力與車速，估算升力係數（`Cl`），並繪製車速與下壓力的關係。

## 輸入來源

- `F_ref`：由前序 `skidpad_test` 自動帶入的目標下壓力（N），不需手動輸入。
- `v_ref`：由前序 `skidpad_test` 自動帶入的目標車速（km/h），不需手動輸入。
- `A_air`：氣動參考面積（m$^2$），需直接輸入且大於零。

空氣密度固定為 $\rho=1.225$ kg/m$^3$。

## 計算方式

先將參考車速由 km/h 換算為 m/s，再由參考下壓力計算係數：

$$
v_{ref, m/s}=\frac{v_{ref, km/h}}{3.6},\qquad
C_l=\frac{F_{ref}}{\frac{1}{2}\rho A v_{ref, m/s}^{2}}
$$

接著以速度掃描計算下壓力：

$$
F_{down}(v)=\frac{1}{2}C_l\rho A v^2
$$

圖上的紅色標記是由 skidpad 傳入的目標參考點。分析輸出 `Cl` 為計算得到的係數，並將 `F_ref` 以 `aero_cl_cd_F_ref_N` 傳給 `tender`，讓兩條分析流程在 Tender 匯合。
