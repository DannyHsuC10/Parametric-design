# ODE Spring 分析

## 分析目的與質量來源

以 RK45 求解無阻尼二自由度四分之一車模型，觀察簧上／簧下位移與總能量守恆。本分析接在 `Analytical_Numerical_Simulation` 後面，並與 `damping_rate` 匯合至 `damping_ode`，後續依序為 `quarter_suspension → Damped_oscillation_analysis`，使用相同的簧上總質量設定。

## Python 固定設定

以下常數直接設定於 `analysis/ode_spring.py` 檔案頂端：

- `TIRE_STIFFNESS_N_PER_M = 100000.0`：輪胎剛度，單位 N/m。
- `INITIAL_STATE = (0.0, 0.0, 0.025, 0.0)`：依序為簧上位移、簧上速度、簧下位移、簧下速度，單位分別為 m、m/s、m、m/s。
- `SIMULATION_TIME_S = 5.0`：模擬結束時間，單位 s。
- `OUTPUT_TIME_STEP_S = 0.001`：輸出取樣間距，單位 s。
- `RK45_RTOL = 0.001`、`RK45_ATOL = 0.000001`：求解器相對與絕對容許誤差，保留原程式設定。

RK45 會自動調整內部積分步長；輸出取樣間距與 Euler 積分步長的意義不同。

## 運動方程式

位移以靜態平衡位置為零點，路面保持不動：

$$
m_s\ddot{x}_s=-k_s(x_s-x_u)
$$

$$
m_u\ddot{x}_u=k_s(x_s-x_u)-k_tx_u
$$

此模型包含懸吊彈簧與輪胎彈簧，未加入阻尼。重力造成的靜態壓縮已由平衡位置吸收。

## 能量與結果

$$
E=\frac{1}{2}m_s\dot{x}_s^2+\frac{1}{2}m_u\dot{x}_u^2+\frac{1}{2}k_s(x_s-x_u)^2+\frac{1}{2}k_tx_u^2
$$

圖表依序顯示簧上／簧下位移、總能量及相對初始能量的百分比誤差。輸出包含實際使用的懸吊剛度 `simulation_rk45_stiffness_used_N_per_m`、初始能量、最大絕對能量誤差，以及簧上／簧下最大絕對位移。

初始能量為零時，能量誤差以零記錄。若求解器失敗，主程式會顯示原因；所有結果由主程式統一儲存至本資料夾。
