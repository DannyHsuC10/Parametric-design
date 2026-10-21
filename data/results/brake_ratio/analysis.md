# Brake_ratio：理想分配

以正值 $z$ 表示減速度的 g 倍數，$f$ 為靜態前軸配重，$W=mg$：

$$N_f=Wf+Wzh/L,\qquad N_r=W(1-f)-Wzh/L$$

$$F_{bf}=zN_f,\qquad F_{br}=zN_r$$

掃描上限為輪胎摩擦係數與後軸離地界限兩者較小值：$z_{max}=\min(\mu_w,(1-f)L/h)$；當 $h=0$ 時不設離地上限。沿用原本十點、通過原點的最小平方擬合：$k=\sum F_{bf}F_{br}/\sum F_{bf}^2$，等效前軸比例為 $1/(1+k)$。這是整段理想曲線的固定比例近似，不代表 Balance bar 的機械設定。
