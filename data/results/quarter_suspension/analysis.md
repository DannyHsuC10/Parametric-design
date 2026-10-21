# quarter_suspension 分析

## 分析目的與流程

接在 damping_ode 後面，與 quarter_suspension_int 匯合至 Damped_oscillation_analysis。使用 RK45 計算有阻尼四分之一車的路面階躍響應，保留位置、速度、加速度與能量四個面板。

## 參數來源

簧上質量為 ms 除以 4，單輪簧下質量為 mu。懸吊彈簧剛度 Ks 自動取自 Tire stiffness，輪胎剛度取 CSV 的 Kt。阻尼比自動取自 damping_rate 的解出量 damping_rate_best_ratio；Ks 與最佳阻尼比均不提供輸入框，也不在 CSV 手動設定。結果中的 quarter_ode_ratio_used 記錄實際使用的值。

$$
c_{ref}=2\sqrt{m_sK_s},\qquad c_s=\zeta c_{ref}
$$

此公式是簧上單自由度參考尺度，不是整個二自由度系統所有模態的臨界阻尼。

## 運動方程式

座標相對於原先的靜態平衡位置：

$$
m_s\ddot{x}_s=-K_s(x_s-x_u)-c_s(\dot{x}_s-\dot{x}_u)
$$

$$
m_u\ddot{x}_u=K_s(x_s-x_u)+c_s(\dot{x}_s-\dot{x}_u)-K_t(x_u-x_r)
$$

## 能量

輪胎彈性能量使用輪胎相對於路面的變形：

$$
E=\frac{1}{2}m_s\dot{x}_s^2+\frac{1}{2}m_u\dot{x}_u^2+\frac{1}{2}K_s(x_s-x_u)^2+\frac{1}{2}K_t(x_u-x_r)^2
$$

原檔使用 xu 計算輪胎能量；整合時改為 xu-xr，與路面階躍模型一致。路面移動會對系統做功，因此階躍當下的能量變化不是單純的阻尼耗散。

## Python 固定設定

於 analysis/quarter_suspension.py 檔案頂端設定全零初始狀態、模擬時間 1 s、輸出 2000 點、路面於 0.1 s 抬升 0.05 m。RK45 容許誤差保留原檔的相對 0.0000001、絕對 0.000000001，並在路面階躍處分段積分。

## 圖表與輸出

輸出使用的 Ks、參考臨界阻尼、阻尼係數、峰值絕對簧上加速度、末時刻簧上位移與能量。
