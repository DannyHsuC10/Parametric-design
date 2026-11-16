# 懸吊剛性、自然頻率與彈簧

[返回主報告](README.md) · [上一篇：Skidpad 與空力需求](02_skidpad_aero.md) · [下一篇：Anti、Roll Center 與轉向幾何](04_geometry_steering.md)

## 3. 指定 Pitch／Roll 角度所需剛性

$$
s=\frac{\ell}{2}\theta,\quad \mathcal{M}=M_s|a_g|gh,\quad K=\frac{\mathcal{M}}{\ell s}
$$

### Pitch

$$
s=\frac{\ell}{2}\theta
$$

$$
s=\frac{1.53}{2}\cdot0.0261799387799=0.0200276531666\ \mathrm{m}
$$

$$
K=\frac{M_s|a_g|gh}{\ell s}
$$

$$
K=\frac{260.55\cdot2\cdot9.81\cdot0.3}{1.53\cdot0.0200276531666}=50048.3590429\ \mathrm{N/m}
$$

### Roll

$$
s=\frac{\ell}{2}\theta
$$

$$
s=\frac{1.25}{2}\cdot0.0349065850399=0.0218166156499\ \mathrm{m}
$$

$$
K=\frac{M_s|a_g|gh}{\ell s}
$$

$$
K=\frac{260.55\cdot2.2\cdot9.81\cdot0.3}{1.25\cdot0.0218166156499}=61859.5315449\ \mathrm{N/m}
$$

此處 K 是原角度分析的等效需求剛性；與單支彈簧簧率不同。

## 4. Compressed travel：行程限制

### Pitch

$$
K_{\mathrm{travel}}=\frac{M_s|a_g|gh}{\ell d}
$$

$$
K_{\mathrm{travel}}=\frac{260.55\cdot2\cdot9.81\cdot0.3}{1.53\cdot0.025}=40094.0470588\ \mathrm{N/m}
$$

$$
\theta_{\mathrm{travel}}=\arctan\left(\frac{2d}{\ell}\right)\frac{180}{\pi}
$$

$$
\theta_{\mathrm{travel}}=\arctan\left(\frac{2\cdot0.025}{1.53}\right)\frac{180}{\pi}=1.87174496529^\circ
$$

### Roll

$$
K_{\mathrm{travel}}=\frac{M_s|a_g|gh}{\ell d}
$$

$$
K_{\mathrm{travel}}=\frac{260.55\cdot2.2\cdot9.81\cdot0.3}{1.25\cdot0.025}=53982.62496\ \mathrm{N/m}
$$

$$
\theta_{\mathrm{travel}}=\arctan\left(\frac{2d}{\ell}\right)\frac{180}{\pi}
$$

$$
\theta_{\mathrm{travel}}=\arctan\left(\frac{2\cdot0.025}{1.25}\right)\frac{180}{\pi}=2.29061004264^\circ
$$

## 5. Frequency vs stiffness：較高需求剛性

### Pitch

$$
K_{\mathrm{selected}}=\max(K_{\mathrm{angle}},K_{\mathrm{travel}})
$$

$$
K_{\mathrm{selected}}=\max(50048.3590429,40094.0470588)=50048.3590429\ \mathrm{N/m}
$$

$$
f_n=\frac{1}{2\pi}\sqrt{\frac{K_{\mathrm{selected}}}{M_s/2}}
$$

$$
f_n=\frac{1}{2\pi}\sqrt{\frac{50048.3590429}{260.55/2}}=3.11949656715\ \mathrm{Hz}
$$

### Roll

$$
K_{\mathrm{selected}}=\max(K_{\mathrm{angle}},K_{\mathrm{travel}})
$$

$$
K_{\mathrm{selected}}=\max(61859.5315449,53982.62496)=61859.5315449\ \mathrm{N/m}
$$

$$
f_n=\frac{1}{2\pi}\sqrt{\frac{K_{\mathrm{selected}}}{M_s/2}}
$$

$$
f_n=\frac{1}{2\pi}\sqrt{\frac{61859.5315449}{260.55/2}}=3.46811032219\ \mathrm{Hz}
$$

## 6. Tire stiffness：輪胎柔度與彈簧簧率

$$
K_w=K_sMR^2,\qquad K_r=\frac{K_wK_t}{K_w+K_t}
$$

### Pitch：使用兩條輪胎的等效剛性

$$
K_{s,j}=\frac{K_j(2K_t)}{(2K_t-K_j)MR^2}
$$

$$
K_{s,j}=\frac{50048.3590429\cdot(2\cdot80000)}{(2\cdot80000-50048.3590429)\cdot1^2}=72829.6310738\ \mathrm{N/m}
$$

### Roll：使用兩條輪胎的等效剛性

$$
K_{s,j}=\frac{K_j(2K_t)}{(2K_t-K_j)MR^2}
$$

$$
K_{s,j}=\frac{61859.5315449\cdot(2\cdot80000)}{(2\cdot80000-61859.5315449)\cdot1^2}=100850.599177\ \mathrm{N/m}
$$

$$
K_{\mathrm{ride,target}}=\frac{K_p+K_{\mathrm{roll}}}{4}
$$

$$
K_{\mathrm{ride,target}}=\frac{50048.3590429+61859.5315449}{4}=27976.972647\ \mathrm{N/m}
$$

一般 Ks 沿用原模型：20,000～80,000 N/m 之間 2,000 個等距候選，選 ride rate 誤差最小者。

$$
K_s^*=\mathrm{argmin}_{K_s}\left|\frac{K_sMR^2K_t}{K_sMR^2+K_t}-K_{\mathrm{ride,target}}\right|
$$

$$
K_s^*=43021.5107554\ \mathrm{N/m},\qquad K_{\mathrm{ride,actual}}=27976.5777489\ \mathrm{N/m}
$$

## 7. Frequency vs mass：簧上與簧下頻率

$$
K_{s,\mathrm{eq}}=\frac{K_{s,\mathrm{roll}}+K_{s,\mathrm{pitch}}}{4}
$$

$$
K_{s,\mathrm{eq}}=\frac{100850.599177+72829.6310738}{4}=43420.0575626\ \mathrm{N/m}
$$

$$
K_w=K_{s,\mathrm{eq}}MR^2,\quad K_r=\frac{K_wK_t}{K_w+K_t}
$$

$$
K_w=43420.0575626\cdot1^2=43420.0575626,\quad K_r=\frac{43420.0575626\cdot80000}{43420.0575626+80000}=28144.5712602\ \mathrm{N/m}
$$

$$
f_s=\frac{1}{2\pi}\sqrt{\frac{K_r}{M_s/4}},\quad f_u=\frac{1}{2\pi}\sqrt{\frac{K_t+K_w}{m_u}}
$$

$$
f_s=\frac{1}{2\pi}\sqrt{\frac{28144.5712602}{260.55/4}}=3.30827731656\ \mathrm{Hz},\quad{}f_u=\frac{1}{2\pi}\sqrt{\frac{80000+43420.0575626}{14.4}}=14.7343763285\ \mathrm{Hz}
$$

$$
\mathrm{unsprung\ ratio}=\frac{m_u}{M_s/4+m_u}\cdot100
$$

$$
\mathrm{unsprung\ ratio}=\frac{14.4}{260.55/4+14.4}\cdot100=18.1046676096\%
$$

## 8. 固定 Roll，反算 Heave

$$
f_{\mathrm{target}}=\frac{f_{u,0}}{N}
$$

$$
f_{\mathrm{target}}=\frac{14.7343763285}{5}=2.94687526569\ \mathrm{Hz}
$$

$$
K_{r,\mathrm{target}}=(2\pi f_{\mathrm{target}})^2\frac{M_s}{4}
$$

$$
K_{r,\mathrm{target}}=(2\pi\cdot2.94687526569)^2\frac{260.55}{4}=22331.3166652\ \mathrm{N/m}
$$

$$
K_{h,\mathrm{target}}=\frac{4K_{r,\mathrm{target}}K_t}{(K_t-K_{r,\mathrm{target}})MR^2}-K_{s,\mathrm{roll}}
$$

$$
K_{h,\mathrm{target}}
$$

$$
K_{h,\mathrm{target}}=\frac{4\cdot22331.3166652\cdot80000}{(80000-22331.3166652)\cdot1^2}-100850.599177=23064.5124514\ \mathrm{N/m}
$$

$$
\lambda_h=\frac{K_{h,\mathrm{target}}}{K_{\mathrm{main}}},\quad\Delta K_h=K_{\mathrm{main}}-K_{h,\mathrm{target}}
$$

$$
\lambda_h=\frac{23064.5124514}{72829.6310738}=0.3166913262,\quad\Delta K_h=72829.6310738-23064.5124514=49765.1186224\ \mathrm{N/m}
$$

$$
\mathrm{reduction}=(1-\lambda_h)100
$$

$$
\mathrm{reduction}=(1-0.3166913262)\cdot100=68.33086738\%
$$

以新 Heave 和固定 Roll 代回第 7 節的同一公式，回算頻率如下。

| 調整後簧上頻率 Hz | 調整後簧下頻率 Hz |
| --- | --- |
| 2.94687526569 | 13.972008933 |

## 9. 主 Heave 與 Tender 串聯

$$
K_{\mathrm{series}}=\frac{K_{\mathrm{main}}K_{\mathrm{tender}}}{K_{\mathrm{main}}+K_{\mathrm{tender}}},\quad{}K_{\mathrm{tender}}=\frac{K_{\mathrm{series,target}}K_{\mathrm{main}}}{K_{\mathrm{main}}-K_{\mathrm{series,target}}}
$$

$$
K_{\mathrm{tender}}
$$

$$
K_{\mathrm{tender}}=\frac{23064.5124514\cdot72829.6310738}{72829.6310738-23064.5124514}=33754.1631414\ \mathrm{N/m}
$$

$$
\rho_t=\frac{K_{\mathrm{tender}}}{K_{\mathrm{main}}}
$$

$$
\rho_t=\frac{33754.1631414}{72829.6310738}=0.463467446474,\quad K_{\mathrm{series}}=23064.5124514\ \mathrm{N/m}
$$

串聯剛性僅適用於 Tender 未併圈階段。

---

[返回主報告](README.md) · [上一篇：Skidpad 與空力需求](02_skidpad_aero.md) · [下一篇：Anti、Roll Center 與轉向幾何](04_geometry_steering.md)
