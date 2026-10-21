# Time Sensitivity 分析

## 分析目的與參數來源

對同一個無阻尼單自由度模型掃描 Euler 時間步長，比較位移、總能量及能量誤差。流程由 `Tire stiffness` 分支至本分析，剛度直接使用該分析輸出的 `Ks`，單位 N/m；`Ks` 自動傳入，不提供輸入框。

後續分成 `Critical_Damping_Analysis → damping_rate` 與 `Analytical_Numerical_Simulation → ode_spring` 兩路。`damping_rate` 一路接 `damping_int → quarter_suspension_int`，另一路與 `ode_spring` 匯合到 `damping_ode → quarter_suspension`。兩個 quarter suspension 分析最後匯合至 `Damped_oscillation_analysis`。

唯一可輸入的參數為 `ms`，表示四輪簧上總質量，預設 260 kg。實際分析使用四分之一簧上質量：

$$
m=\frac{m_{s,total}}{4},\qquad k=K_s,\qquad \omega_n=\sqrt{\frac{K_s}{m}}
$$

此處的 `Ks` 是 `Tire stiffness` 圖上所選的彈簧剛度，直接用於單自由度彈簧質量模型。

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
