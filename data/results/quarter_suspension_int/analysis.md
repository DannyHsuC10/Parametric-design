# quarter_suspension_int 分析

## 分析目的與流程

接在 damping_int 後面，以半隱式 Euler 模擬四分之一車通過階躍路面。本分析與 quarter_suspension 最後匯合至 Damped_oscillation_analysis。

## 參數來源

- ms：四輪簧上總質量，分析使用四分之一。
- mu：單輪簧下質量。
- Ks：直接讀取 Tire stiffness 輸出的懸吊彈簧剛度，不提供輸入框。
- Kt：CSV 中的輪胎剛度。
- damping_rate_best_ratio：自動讀取 damping_rate 選出的最佳候選阻尼比，不提供輸入框，也不在 CSV 手動設定。結果中的 quarter_int_ratio_used 記錄實際使用的值。

$$
m_s=\frac{m_{s,total}}{4},\qquad c=2\zeta\sqrt{m_sK_s}
$$

此處以簧上單自由度公式定義阻尼比的參考尺度；不代表二自由度車身與輪跳兩個模態同時臨界阻尼。

## 靜態平衡與運動方程式

座標包含重力造成的靜態下沉，原始路面高度為零：

$$
z_{u,0}=-\frac{(m_s+m_u)g}{K_t},\qquad z_{s,0}=z_{u,0}-\frac{m_sg}{K_s}
$$

$$
m_s\ddot{z}_s=-m_sg+K_s(z_u-z_s)+c(\dot{z}_u-\dot{z}_s)
$$

$$
m_u\ddot{z}_u=-m_ug-K_s(z_u-z_s)-c(\dot{z}_u-\dot{z}_s)+K_t(z_r-z_u)
$$

原程式先更新速度，再用新速度更新位置，保留為半隱式 Euler：

$$
v_{n+1}=v_n+a_n\Delta t,\qquad z_{n+1}=z_n+v_{n+1}\Delta t
$$

## Python 固定設定

於 analysis/quarter_suspension_int.py 檔案頂端設定模擬時間 5 s、步長 0.001 s、初始速度皆為零；採用原程式 t > 1 s 後路面抬升 0.05 m 的條件。初始位置由靜態平衡計算，不需要手動輸入。

## 圖表與輸出

顯示簧上絕對座標位置與加速度，並以虛線標示原始平衡位置及路面階躍時間。輸出使用的 Ks、阻尼係數、靜態位置、最大位置、最大帶正負號加速度與最大絕對加速度。負位移及負加速度均保留。
