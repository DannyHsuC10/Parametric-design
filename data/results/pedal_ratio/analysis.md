# Pedal_ratio｜踏板比與液壓需求

理想前軸比例 $\beta_f$ 用於分配比較曲線的總軸扭矩；$T_{\Sigma}$ 表示前後軸扭矩總和：

$$
T^*_{f}=\beta_fT_{\Sigma},
\qquad
T^*_{r}=(1-\beta_f)T_{\Sigma}.
$$

由軸煞車力換算單輪需求扭矩，再由碟盤有效半徑換算需求壓力：

$$
T_{w,i}=\frac{B_iR_{tire}}{2},
\qquad
r_e=\frac{D_{disc}}{2}-d_{gap},
$$

$$
A_{c,i}=n_i\frac{\pi D_{c,i}^2}{4},
\qquad
P_{req,i}=\frac{T_{w,i}}{A_{c,i}\mu_{pad}r_e}.
$$

其中 $A_{c,i}$ 為單顆對向固定式卡鉗兩側活塞面積總和；每軸的兩個車輪各自承受其單輪扭矩。總泵面積及所需總泵推力為

$$
A_{m,i}=\frac{\pi D_{m,i}^2}{4},
\qquad
F_{m,i}=P_{req,i}A_{m,i}.
$$

令 $b$ 為 Balance bar 分配至前總泵的踏板推力比例，$F_d$ 為車手踏力，$SF$ 為設計安全係數。能同時滿足前後回路需求的踏板比為

$$
PR_{req}=\frac{SF}{F_d}
\max\!\left(\frac{F_{m,f}}{b},\frac{F_{m,r}}{1-b}\right).
$$

此踏板比與 Balance bar 推力分配決定設定踏力下的前後回路壓力：

$$
P_{line,f}=\frac{F_dPR_{req}b}{A_{m,f}},
\qquad
P_{line,r}=\frac{F_dPR_{req}(1-b)}{A_{m,r}}.
$$

理想固定煞車力比例 $\beta_f$ 和 Balance bar 推力比例 $b$ 是不同的量，前者描述輪胎端的煞車力分配，後者描述總泵端的機械推力分配。模型採理想液壓傳遞，不含管路壓損。
