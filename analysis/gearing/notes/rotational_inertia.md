# Rotational_inertia：齒輪旋轉慣量

各齒輪以空心圓盤近似。$m_n$ 為模數、$d_{shaft}$ 為軸徑、$b_j$ 為齒寬，輸入單位均為 mm；$\rho$ 為材料密度，單位 kg/m³。

$$r_{o,j}=\frac{m_nZ_j}{2000},\qquad r_i=\frac{d_{shaft}}{2000},\qquad w_j=\frac{b_j}{1000}$$

$$M_j=\rho\pi(r_{o,j}^2-r_i^2)w_j$$

$$J_j=\frac{1}{2}M_j(r_{o,j}^2+r_i^2)$$

依程式的齒比平方折算：

$$i_2=\frac{Z_r}{Z_{p2}},\qquad i=\frac{Z_{p1}}{Z_s}i_2$$

$$J_{p,eq}=i_2^2(J_{p1}+J_{p2}),\qquad J_{s,eq}=i^2J_s$$

$$J_{total}=N_pJ_{p,eq}+J_{s,eq}$$

慣量單位為 kg·m²；總量包含太陽輪與 $N_p$ 組行星輪的上述折算值，未另加齒圈及行星架慣量。
