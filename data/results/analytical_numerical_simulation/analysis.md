# Analytical Numerical Simulation 分析

## 分析目的

比較無阻尼單自由度彈簧質量系統的解析解與顯式 Euler 數值解，並顯示絕對位移誤差及逐點相對誤差。

本分析直接接在 `Time_sensitivity` 後面，後續依序為 `ode_spring → damping_ode → quarter_suspension → Damped_oscillation_analysis`。`damping_ode` 同時連接 `damping_rate` 以取得最佳候選阻尼比；最後的 `Damped_oscillation_analysis` 同時連接 `quarter_suspension_int`。

## 輸入與質量定義


輸入框與參數 CSV 只保留上述質量設定。分析使用四分之一簧上質量，並輸出為 `simulation_corner_mass_kg`：

$$
m=\frac{m_{s,total}}{4},\qquad \omega_n=\sqrt{\frac{k}{m}},\qquad f_n=\frac{\omega_n}{2\pi}
$$

懸吊彈簧剛度直接使用 `Tire stiffness` 輸出的 `Ks`，即上述方程式中的 $k=K_s$。`Ks` 自動傳入，不提供輸入框；與 `Time_sensitivity`、`ode_spring` 使用相同的懸吊彈簧剛度。

## Python 固定設定

以下常數直接設定於 `analysis/Analytical_Numerical_Simulation.py` 檔案頂端：

- `INITIAL_DISPLACEMENT_M = 0.05`、`INITIAL_VELOCITY_M_PER_S = 0.0`：初始位移與速度。
- `SIMULATION_TIME_S = 5.0`：模擬結束時間，單位 s。
- `TIME_STEP_S = 0.00001`：顯式 Euler 時間步長，單位 s。

## 解析解與數值更新

位移相對於原先靜態平衡位置，方程式為：

$$
m\ddot{x}+kx=0
$$

解析解與 Euler 更新式為：

$$
x(t)=x_0\cos(\omega_nt)+\frac{v_0}{\omega_n}\sin(\omega_nt)
$$

$$
x_{n+1}=x_n+v_n\Delta t,\qquad v_{n+1}=v_n-\frac{k}{m}x_n\Delta t
$$

兩個更新式均使用上一步的狀態，保留原程式的顯式 Euler 方法。

## 圖表與輸出

圖表合併為三個面板：解析／數值位移比較、絕對誤差、相對誤差。輸出包括實際使用剛度 `simulation_euler_stiffness_used_N_per_m`、自然頻率、最大絕對誤差、RMS 誤差、最大相對誤差及末時刻能量誤差。

$$
e_{abs}=|x_{num}-x_{exact}|,\qquad e_{rel}=\frac{e_{abs}}{|x_{exact}|+10^{-12}}\times100\%
$$

解析位移接近零時，相對誤差會放大，應搭配絕對誤差判讀。輸出圖片與數值由主程式統一儲存至本結果資料夾。
