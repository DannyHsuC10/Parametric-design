# damping_ode 分析

## 分析目的與流程

由 ode_spring 與 damping_rate 兩路匯合進入本分析，以 RK45 求解單自由度阻尼振動，並保留時間歷程與位移／速度相圖。後續依序為 quarter_suspension → Damped_oscillation_analysis；阻尼比自動讀取 damping_rate 的最佳候選結果。

## 參數與剛度來源

簧上總質量使用 ms，分析時除以 4；Ks 自動取自 Tire stiffness。原檔的 Kr 與 cr 改由以下關係計算：

$$
m=\frac{m_{s,total}}{4},\qquad K_w=K_sMR^2,\qquad K_r=\frac{K_wK_t}{K_w+K_t}
$$

$$
\omega_n=\sqrt{\frac{K_r}{m}},\qquad f_n=\frac{\omega_n}{2\pi},\qquad c=2\zeta\sqrt{mK_r}
$$

Kt 與 MR 使用既有 CSV 參數；阻尼比自動取自 damping_rate 的解出量 damping_rate_best_ratio，再依此模型的 Kr 換算阻尼係數。Ks 與最佳阻尼比都不提供輸入框，也不在 CSV 手動設定。結果中的 damping_ode_ratio_used 記錄實際使用的值。

## 運動方程式

位移相對於靜態平衡位置，重力的靜態壓縮已吸收於零點。

$$
m\ddot{x}+c\dot{x}+K_rx=0
$$

阻尼比分別小於、等於、大於 1 時，為欠阻尼、臨界阻尼、過阻尼。這是單自由度模型的分類。

## Python 固定設定

於 analysis/damping_ode.py 檔案頂端設定初始狀態 (1 m, 0 m/s)、模擬時間 20 s、輸出 4001 點、RK45 相對容許誤差 0.000001 與絕對容許誤差 0.00000001。

RK45 內部使用自適應步長；輸出點數僅控制圖表取樣。

## 圖表與輸出

同一張結果圖包含位移時間歷程與相圖。輸出使用的 Kr、阻尼係數、阻尼比、自然頻率與末時刻位移。原檔的兩張圖整合為同一分析結果圖。
