# acc_resis：行駛阻力與起步齒比

$r_w$ 為輪胎半徑，$J_w$ 為單輪旋轉慣量，$c_r$、$c_s$ 為滾阻與車身起步阻力係數。

$$a=\mu_wg,\qquad v=\frac{V_t}{3.6}$$

$$F_I=\frac{J_wa}{r_w^2},\qquad F_{start}=\frac{T_{start}}{r_w},\qquad F_{roll}=c_rmg$$

$$F_{body,start}=c_smg,\qquad F_{grade}=mg\sin\alpha$$

以車高 $H$、車寬 $B$ 估算迎風面積 $A=HB$，空氣阻力包含下列兩項：

$$F_{air}=\frac{1}{2}C_d\rho_{air}Av^2+6\pi\sqrt{H^2+B^2}\,\mu_{air}v$$

$$\rho_{air}=1.225\ \mathrm{kg/m^3},\qquad \mu_{air}=1.81\times10^{-5}\ \mathrm{Pa\cdot s}$$

依目前程式的車身／輪端分組方式加總：

$$F_{body}=F_{body,start}+F_{grade}+F_{air},\qquad F_{wheel}=F_{roll}+F_{start}+F_I$$

$$F_{req}=\frac{F_{body}/4+F_{wheel}}{\eta}$$

$$T_{req}=F_{req}r_w,\qquad i_{min}=\frac{1.1T_{req}}{T_m}$$

力、扭矩分別使用 N、N·m；坡度輸入為 deg，代入三角函數前轉成 rad。上述保留現行程式對各阻力項的分配方式。
