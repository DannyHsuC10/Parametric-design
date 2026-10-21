# Output_check：傳動輸出與加速模擬

使用手動齒數與傳動效率 $\eta$，計算單輪輸出扭矩與最高車速。

$$i=\frac{Z_{p1}}{Z_s}\frac{Z_r}{Z_{p2}},\qquad T_w=T_m i\eta$$

$$v_{max}=\frac{2\pi r_w n_m}{60i},\qquad V_{max}=3.6v_{max}$$

每軸的兩輪驅動力同時受馬達扭矩與輪胎抓地限制：

$$N_r=mgw_f+\frac{mah}{L},\qquad N_f=mg-N_r$$

$$F_{drive}=\min\left(\frac{2T_w}{r_w},\max(0,\mu_wN_f)\right)+\min\left(\frac{2T_w}{r_w},\max(0,\mu_wN_r)\right)$$

$$a_{k+1}=\frac{F_{drive,k}}{m}$$

$$v_{k+1}=\min(v_k+a_{k+1}\Delta t,v_{max}),\qquad x_{k+1}=x_k+v_{k+1}\Delta t$$

初始速度與位移為零，$\Delta t=0.1\ \mathrm{s}$，執行 100 步；載重使用上一步加速度。載重式依現行程式保留，$w_f$ 為輸入的前軸配重，但目前放在後軸靜態項。此模型以前後軸皆有相同驅動輸出估算；速度達上限後，圖中的加速度仍為驅動力除以質量的計算值。
