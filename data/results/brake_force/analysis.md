# Brake_force｜踏力、軸煞車力與首次鎖死

踏板比、Balance bar、總泵、卡鉗與碟盤幾何共同決定踏力至前後軸煞車力的增益。令 $s_f=b$、$s_r=1-b$，則每軸增益可寫成

$$
K_i=PR\frac{s_i}{A_{m,i}}A_{c,i}\mu_{pad}r_e\frac{2}{R_{tire}},
\qquad
B_i=F_dK_i,
\quad i\in\{f,r\}.
$$

其中 $A_{m,i}$ 是總泵面積，$A_{c,i}$ 是單顆卡鉗兩側活塞面積總和，$r_e$ 是碟盤有效半徑。軸荷隨減速度轉移；令 $W=mg$，則

$$
N_f(z)=Wf+\frac{Wzh}{L},
\qquad
N_r(z)=W(1-f)-\frac{Wzh}{L}.
$$

在固定踏板比下，理論減速度由總煞車力與車重決定：

$$
z_{theory}=\frac{B_f+B_r}{W}.
$$

首次鎖死邊界由軸煞車力等於該軸輪胎摩擦極限求得。令 $q=(K_f+K_r)h/L$，前軸與後軸各自的臨界踏力為

$$
F_{lock,f}=\frac{\mu_wWf}{K_f-\mu_wq},
\qquad
F_{lock,r}=\frac{\mu_wW(1-f)}{K_r+\mu_wq}.
$$

若前軸臨界式的分母不為正，該固定分配下前軸不構成有限踏力鎖死界限。全車首次鎖死踏力與對應減速度為

$$
F_{lock}=\min(F_{lock,f},F_{lock,r}),
\qquad
z_{lock}=\frac{F_{lock}(K_f+K_r)}{W}.
$$

這是直線、準靜態的輪胎摩擦邊界，不含鎖死後滑移、ABS、煞車熱衰退或回生煞車動態。
