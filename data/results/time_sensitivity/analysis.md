# Time Sensitivity 分析

## 分析目的與參數來源

對同一個無阻尼單自由度模型掃描 Euler 時間步長，比較位移、總能量及能量誤差。流程由 `Tire stiffness` 分支至本分析，剛度直接使用該分析輸出的 `Ks`，單位 N/m；`Ks` 自動傳入，不提供輸入框。

後續流程依序為 `Analytical_Numerical_Simulation → ode_spring`。

唯一可輸入的參數為 `simulation_ms_total_kg`，表示四輪簧上總質量，預設 260 kg。實際分析使用四分之一簧上質量：

$$
m=\frac{m_{s,total}}{4},\qquad k=K_s,\qquad \omega_n=\sqrt{\frac{K_s}{m}}
$$

此處的 `Ks` 是 `Tire stiffness` 圖上所選的彈簧剛度，直接用於單自由度彈簧質量模型。

## Python 固定設定

以下常數直接設定於 `analysis/Time_sensitivity.py` 檔案頂端：

- `INITIAL_DISPLACEMENT_M = 0.05`、`INITIAL_VELOCITY_M_PER_S = 0.0`：初始位移與速度。
- `SIMULATION_TIME_S = 5.0`：模擬結束時間，單位 s。
- `TIME_STEPS_S = (0.01, 0.001, 0.0001, 0.00001)`：掃描的 Euler 時間步長，單位 s。

## 計算方式

每一個步長分別使用顯式 Euler 積分，總能量為：

$$
E=\frac{1}{2}mv^2+\frac{1}{2}kx^2,\qquad e_E=\frac{E-E_0}{E_0}\times100\%
$$

對固定步長且初始能量非零的無阻尼模型，顯式 Euler 的能量變化符合：

$$
E_{n+1}=\left(1+\omega_n^2\Delta t^2\right)E_n
$$

因此較大步長會出現明顯的數值能量增長；這是積分誤差，不代表模型存在外部能量輸入。縮小時間步長可以減輕模擬期間的漂移。

## 圖表與輸出

每一欄對應一個步長，三列分別顯示位移、能量及能量誤差，保留原本四組圖表的內容。圖表標題與列印資訊顯示實際使用的 `Ks`。輸出包含使用質量、使用剛度 `simulation_sensitivity_stiffness_used_N_per_m`、最細步長、最細／最粗步長的末時刻能量誤差，以及最細步長的最大位移誤差。

若初始位移與速度皆為零，系統保持平衡，能量誤差以零記錄。時間網格包含結束時刻；若結束時間不是步長的整數倍，最後一步使用剩餘時間。
