# Acc_load：加速載重轉移

以全車質量 $m$、軸距 $L$、重心高度 $h$ 與輪胎摩擦係數 $\mu_w$，計算加速時的前後軸法向載重。

$$0\leq a\leq a_{max}=\mu_w g$$

$$\Delta N=\frac{mah}{L}$$

$$N_r=mgw_f+\Delta N,\qquad N_f=mg-N_r$$

$w_f$ 為 `hl_front_weight_ratio`。以上依現行程式整理，其靜態項目前將 $mgw_f$ 計入後軸；前後軸配重的定義需另核對。

質量單位為 kg，長度為 m，載重為 N，$g=9.81\ \mathrm{m/s^2}$。
