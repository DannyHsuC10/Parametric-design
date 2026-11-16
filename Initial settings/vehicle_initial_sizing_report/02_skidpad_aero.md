# Skidpad 與空力需求

[返回主報告](README.md) · [上一篇：輸入參數、質量與重心](01_inputs_cg.md) · [下一篇：懸吊剛性、自然頻率與彈簧](03_suspension_stiffness.md)

## 2. Skidpad：目標圈速與所需下壓力

$$
R_{\mathrm{skid}}=\frac{D}{2},\quad v=\frac{\pi D}{T}
$$

$$
R_{\mathrm{skid}}=\frac{18.25}{2}=9.125\ \mathrm{m},\quad v=\frac{\pi\cdot18.25}{5}=11.4668131856\ \mathrm{m/s}
$$

$$
a_y=\frac{v^2}{R_{\mathrm{skid}}},\quad \mu_{\mathrm{req}}=\eta\frac{a_y}{g}
$$

$$
a_y=\frac{11.4668131856^2}{9.125}=14.4096224256\ \mathrm{m/s^2},\quad\mu_{\mathrm{req}}=1.4\frac{14.4096224256}{9.81}=2.05641910253
$$

$$
F_{\mathrm{raw}}=\left(\frac{\mu_{\mathrm{req}}}{\mu_y}-1\right)Mg
$$

$$
F_{\mathrm{raw}}=\left(\frac{2.05641910253}{1.81526957993}-1\right)\cdot318.15\cdot9.81=414.616147129\ \mathrm{N}
$$

$$
F_{\mathrm{down}}=\max(0,F_{\mathrm{raw}})
$$

$$
F_{\mathrm{down}}=\max(0,414.616147129)=414.616147129\ \mathrm{N}
$$

## 2.4 空力有效面積與目標係數

$$
F=C\rho Av^2,\qquad C=\frac{F}{\rho Av^2}
$$

$$
C=\frac{414.616147129}{1.225\cdot1\cdot11.4668131856^2}=2.57409545977
$$

$$
F=\frac{1}{2} Cl\rho Av^2,\qquad Cl=2C
$$

$$
Cl=2\cdot2.57409545977=5.14819091953
$$

係數以下壓力為正；C 採指定公式，Cl 對照原 Aero_Cl_Cd 定義。完整需求不乘下壓力施加比例。

---

[返回主報告](README.md) · [上一篇：輸入參數、質量與重心](01_inputs_cg.md) · [下一篇：懸吊剛性、自然頻率與彈簧](03_suspension_stiffness.md)
