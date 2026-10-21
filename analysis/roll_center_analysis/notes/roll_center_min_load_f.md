# roll_center_min_load_f：前軸最低載重轉移率峰值

共用簧上質量、由 `cog_total_Ixx_kg_m2` 提供的全車 Ixx 慣量（含簧下元件、相對全車重心），重心高度與前軸懸吊剛性。前軸獨立半車模型使用一半全車 Ixx；前軸簧上承載比例 $f_s$ 用於分配質量。等效線性剛性 $k_s=K_{s,roll}MR_f^2$，車架路徑 $k_c=ck_s$。

$$m_f=m_sf_s,\qquad I_f=\frac{I_{xx,total}}{2}$$

使用側向階躍 $a_y=-\mathrm{ay}\,g$。以輪距 $t_w$ 將側傾角 $\phi$ 轉為等效位移，車架位移為 $x_c$：

$$I_f\ddot{\phi}+k_st_w^2\phi=a_y m_f(h_{cg}-h_{rc})$$

$$\frac{m_f}{4}\ddot{x}_c+k_cx_c=-\frac{a_y m_fh_{rc}}{t_w}$$

由零初始狀態的解析階躍解計算兩路轉移力：

$$\omega_s=\sqrt{\frac{k_st_w^2}{I_f}},\qquad \omega_c=\sqrt{\frac{4k_c}{m_f}}$$

$$A_s=-\frac{a_y m_f(h_{cg}-h_{rc})}{t_w},\qquad A_c=-\frac{a_y m_fh_{rc}}{t_w}$$

$$F_s=A_s(1-\cos\omega_s\tau),\qquad F_c=A_c(1-\cos\omega_c\tau)$$

各路僅取第一個同向半正弦轉移率脈衝，再於共同時間軸加總：

$$R_j(\tau)=A_j\omega_j\sin(\omega_j\tau),\quad 0\leq\tau\leq\frac{\pi}{\omega_j}$$

脈衝區間外令 $R_j=0$，掃描 RC 高度以找出：

$$h_{rc,f}^{*}=\mathrm{argmin}_{h_{rc}}\max_{\tau}|R_s(\tau)+R_c(\tau)|$$

目標單位為 N/s，是轉移率峰值；全時域轉移力另存 CSV。掃描範圍固定為 1%～99% 重心高度，共 50 點；模擬取樣間隔固定 0.001 s，總時間固定 2 s。這些設定不顯示為輸入欄位。最佳高度同時輸出為 `hl_front_roll_center_m`，供後續 Roll／阻尼分析使用。脈衝圖呈現最佳高度下的懸吊、車架及總轉移率。

原始程式的角度／位移改為以 $t_w\phi$ 明確換算，使共用線性剛性保持 N/m；改用解析解避免 Euler 步長誤差。首脈衝加總涵蓋兩路各自的完整第一脈衝，並處理 RC 為零、RC 等於重心高度及零側向加速度的情況。無阻尼、無輪胎與簧下動態；分析軸模型直接使用一半全車 Ixx，是獨立兩路的簡化比較假設。當 ay 為零時沒有唯一最佳高度。
