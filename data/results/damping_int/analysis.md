# damping_int 分析

## 分析目的與流程

由 Time Sensitivity 經 Critical_Damping_Analysis → damping_rate 分支進入本分析，再接 quarter_suspension_int，最後匯合至 Damped_oscillation_analysis。以顯式 Euler 計算含重力的單自由度阻尼系統，保留原程式的速度與位移皆使用上一步狀態更新的方法。

## 參數來源

- ms：四輪簧上總質量，分析時除以 4。
- Ks：自動讀取 Tire stiffness 的解出量，不提供輸入框。
- Kt、MR：沿用參數 CSV 中的輪胎剛度與 motion ratio。
- damping_rate_best_ratio：自動讀取 damping_rate 選出的最佳候選阻尼比，不提供輸入框，也不在 CSV 手動設定。

原程式的 Kr 為單自由度等效乘適剛度，本分析由懸吊彈簧與輪胎串聯計算：

$$
m=\frac{m_{s,total}}{4},\qquad K_w=K_sMR^2,\qquad K_r=\frac{K_wK_t}{K_w+K_t}
$$

原程式的 cr 由阻尼比換算，單位為 N s/m：

$$
c_{critical}=2\sqrt{mK_r},\qquad c=\zeta c_{critical}
$$

其中阻尼比使用上游的 damping_rate_best_ratio。結果中的 damping_int_ratio_used 記錄本次實際使用的值。

## 運動方程式

本分析保留重力項，位移零點尚未扣除靜態壓縮。負位移可正常出現。

$$
m\ddot{x}+c\dot{x}+K_rx+mg=0,\qquad x_{eq}=-\frac{mg}{K_r}
$$

$$
v_{n+1}=v_n+a_n\Delta t,\qquad x_{n+1}=x_n+v_n\Delta t
$$
