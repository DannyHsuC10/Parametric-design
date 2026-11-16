# Anti、Roll Center 與轉向幾何

[返回主報告](README.md) · [上一篇：懸吊剛性、自然頻率與彈簧](03_suspension_stiffness.md) · [下一篇：空力壓縮與四輪受力](05_aero_wheel_loads.md)

## 9.3 前 Anti-dive 與 9.4 AntiScrub／前後 Anti-lift

前後軸分別使用軸端垂向懸吊剛性 Kz 與車體等效剛性 Kc，單位均為 N/m。Kc 為可獨立修改的固定輸入；初始值由改版前主 Heave 72829.63107381333 N/m、MR = 1 的 10 倍假設估算，非量測值。目前前後使用相同 Heave 彈簧；Roll 的 kf／kr 不套用於此處。

$$
K_{z,i}=K_{h,i}MR^2,\quad K_{\mathrm{eq},i}=(1-a_i)^2K_{z,i}+a_i^2K_{c,i}
$$

$$
\frac{dK_{\mathrm{eq},i}}{da_i}=-2(1-a_i)K_{z,i}+2a_iK_{c,i}=0,\quad{}a_i=\frac{K_{z,i}}{K_{z,i}+K_{c,i}},\quad \alpha_i=1-a_i
$$

### 純 Heave

#### 前軸剛性基準（前 Anti-dive）

$$
K_{z,i}=K_{h,i}MR^2,\quad K_{c,i}=\text{固定輸入}
$$

$$
K_{z,i}=72829.6310738\cdot1^2=72829.6310738\ \mathrm{N/m},\quad K_{c,i}=728296.310738\ \mathrm{N/m}
$$

$$
a_i=\frac{K_{z,i}}{K_{z,i}+K_{c,i}},\quad \alpha_i=1-a_i
$$

$$
a_i=\frac{72829.6310738}{72829.6310738+728296.310738}=0.0909090909091=9.09090909091\%,\quad \alpha_i=1-0.0909090909091=0.909090909091
$$

$$
K_{\mathrm{eq},i,\min}=\frac{K_{z,i}K_{c,i}}{K_{z,i}+K_{c,i}}
$$

$$
K_{\mathrm{eq},i,\min}=\frac{72829.6310738\cdot728296.310738}{72829.6310738+728296.310738}=66208.7555216\ \mathrm{N/m}
$$

#### 後軸剛性基準（AntiScrub 來源）

$$
K_{z,i}=K_{h,i}MR^2,\quad K_{c,i}=\text{固定輸入}
$$

$$
K_{z,i}=72829.6310738\cdot1^2=72829.6310738\ \mathrm{N/m},\quad K_{c,i}=728296.310738\ \mathrm{N/m}
$$

$$
a_i=\frac{K_{z,i}}{K_{z,i}+K_{c,i}},\quad \alpha_i=1-a_i
$$

$$
a_i=\frac{72829.6310738}{72829.6310738+728296.310738}=0.0909090909091=9.09090909091\%,\quad \alpha_i=1-0.0909090909091=0.909090909091
$$

$$
K_{\mathrm{eq},i,\min}=\frac{K_{z,i}K_{c,i}}{K_{z,i}+K_{c,i}}
$$

$$
K_{\mathrm{eq},i,\min}=\frac{72829.6310738\cdot728296.310738}{72829.6310738+728296.310738}=66208.7555216\ \mathrm{N/m}
$$

### AntiScrub 與前後 Anti-lift 的設定

$$
\mathrm{AntiDive}_f=a_f
$$

$$
\mathrm{AntiDive}_f=0.0909090909091=9.09090909091\%
$$

$$
\mathrm{AntiScrub}=a_r\frac{a_{\mathrm{acc}}}{a_x}
$$

$$
\mathrm{AntiScrub}=0.0909090909091\frac{1.2}{2}=0.0545454545455=5.45454545455\%
$$

$$
\mathrm{AntiLift}_r=\mathrm{AntiDive}_f,\quad \mathrm{AntiLift}_f=\mathrm{AntiScrub}
$$

$$
\mathrm{AntiLift}_r=0.0909090909091=9.09090909091\%,\quad{}\mathrm{AntiLift}_f=0.0545454545455=5.45454545455\%
$$

| 設定項目 | 比例 | 百分比 | 來源 |
| --- | --- | --- | --- |
| 前 Anti-dive | 0.0909090909091 | 9.09090909091 | 前軸剛性基準 |
| AntiScrub | 0.0545454545455 | 5.45454545455 | 後軸剛性基準 × a_acc / ax |
| 後 Anti-lift | 0.0909090909091 | 9.09090909091 | 等於前 Anti-dive |
| 前 Anti-lift | 0.0545454545455 | 5.45454545455 | 等於 AntiScrub |

Anti 目前只使用純 Heave 主簧；後軸剛性基準經 a_acc／ax 換算為 AntiScrub，後 Anti-lift 則依指定關係取前 Anti-dive。程式參數 a_acc 對應加速目標，與 ax 均以 g 輸入。此為兩路剛性類比及指定比例設定；幾何硬點與實際煞車力路徑不在此求解。

## 10. 前 Roll Center 與 11. 後 Roll Center

$$
r=\frac{h_{\mathrm{RC},f}}{h}=\frac{1}{1+c},\quad h_{\mathrm{RC},f}=rh
$$

$$
h_{\mathrm{RC},f}=\frac{0.3}{1+10}=0.0272727272727\ \mathrm{m}
$$

$$
h_{\mathrm{RC},r}=h_{\mathrm{RC},f}\frac{w_f}{w_r}\frac{t_r}{t_f}\frac{k_f}{k_r}
$$

$$
h_{\mathrm{RC},r}=0.0272727272727\frac{0.5}{0.5}\frac{1.24}{1.25}\frac{0.55}{0.45}=0.0330666666667\ \mathrm{m}
$$

## 11.1 FVSA 與 Camber gain

保留指定的公尺數值公式。tan 的引數使用公尺數值約定，不能將 d 改成毫米後直接代入；deg/mm 是單位比例換算，最大 Camber 變化採指定的線性外推。

### 前軸

$$
\theta=\arctan\left(\frac{2d}{t}\right)
$$

$$
\theta=\arctan\left(\frac{2\cdot0.025}{1.25}\right)=0.0399786871233\ \mathrm{rad}=2.29061004264^\circ
$$

$$
L_{\mathrm{FVSA}}=\frac{1}{\tan(\theta/(2d))}
$$

$$
L_{\mathrm{FVSA}}=\frac{1}{\tan(0.0399786871233/(2\cdot0.025))}=0.972043272039\ \mathrm{m}
$$

$$
G_\gamma=\arctan\left(\frac{1}{L_{\mathrm{FVSA}}}\right)\frac{180}{\pi}
$$

$$
G_\gamma=\arctan\left(\frac{1}{0.972043272039}\right)\frac{180}{\pi}=45.8122008528\ \mathrm{deg/m}
$$

$$
\Delta\gamma_{\mathrm{FVSA}}=G_\gamma d
$$

$$
\Delta\gamma_{\mathrm{FVSA}}=45.8122008528\cdot0.025=1.14530502132^\circ,\quad G_\gamma=0.0458122008528\ \mathrm{deg/mm}
$$

### 後軸

$$
\theta=\arctan\left(\frac{2d}{t}\right)
$$

$$
\theta=\arctan\left(\frac{2\cdot0.025}{1.24}\right)=0.0403007483038\ \mathrm{rad}=2.30906278903^\circ
$$

$$
L_{\mathrm{FVSA}}=\frac{1}{\tan(\theta/(2d))}
$$

$$
L_{\mathrm{FVSA}}=\frac{1}{\tan(0.0403007483038/(2\cdot0.025))}=0.959593717895\ \mathrm{m}
$$

$$
G_\gamma=\arctan\left(\frac{1}{L_{\mathrm{FVSA}}}\right)\frac{180}{\pi}
$$

$$
G_\gamma=\arctan\left(\frac{1}{0.959593717895}\right)\frac{180}{\pi}=46.1812557805\ \mathrm{deg/m}
$$

$$
\Delta\gamma_{\mathrm{FVSA}}=G_\gamma d
$$

$$
\Delta\gamma_{\mathrm{FVSA}}=46.1812557805\cdot0.025=1.15453139451^\circ,\quad G_\gamma=0.0461812557805\ \mathrm{deg/mm}
$$

## 11.2 純 ay 的輪胎壓縮與額外 Roll

這是各軸獨立的兩輪模型，無 ax、無空力；各軸承載質量依前後重量比例分配。

### 前軸

$$
m_i=Mw_i,\quad F_{y,i}=m_i a_{y,g}g
$$

$$
m_i=318.15\cdot0.5=159.075\ \mathrm{kg},\quad F_{y,i}=159.075\cdot2.2\cdot9.81=3433.15665\ \mathrm{N}
$$

$$
T_i=\frac{F_{y,i}h}{t_i},\quad N_L=\frac{m_ig}{2}-T_i,\quad N_R=\frac{m_ig}{2}+T_i
$$

$$
T_i=\frac{3433.15665\cdot0.3}{1.25}=823.957596\ \mathrm{N},\quad{}N_L=\frac{159.075\cdot9.81}{2}-823.957596=-43.694721,\quad N_R=\frac{159.075\cdot9.81}{2}+823.957596=1604.220471\ \mathrm{N}
$$

$$
\delta_L=\frac{N_L}{K_t},\quad\delta_R=\frac{N_R}{K_t}
$$

$$
\delta_L=\frac{-43.694721}{80000}=-0.0005461840125\ \mathrm{m},\quad\delta_R=\frac{1604.220471}{80000}=0.0200527558875\ \mathrm{m}
$$

$$
\phi_{\mathrm{tire}}=\frac{\delta_R-\delta_L}{t_i}
$$

$$
\phi_{\mathrm{tire}}=\frac{0.0200527558875-(-0.0005461840125)}{1.25}=0.01647915192\ \mathrm{rad}=0.944185854971^\circ
$$

**接地失效：存在負輪載。** 上述負壓縮及 Roll 為線性外推參考；有效接地 Roll 為 None，不代表輪胎可承受拉力。

| 靜態單輪壓縮 m | ay 引起左側增量 m | ay 引起右側增量 m | 接地界限 g | 離地臨界 |
| --- | --- | --- | --- | --- |
| 0.0097532859375 | -0.01029946995 | 0.01029946995 | 2.08333333333 | 否 |

### 後軸

$$
m_i=Mw_i,\quad F_{y,i}=m_i a_{y,g}g
$$

$$
m_i=318.15\cdot0.5=159.075\ \mathrm{kg},\quad F_{y,i}=159.075\cdot2.2\cdot9.81=3433.15665\ \mathrm{N}
$$

$$
T_i=\frac{F_{y,i}h}{t_i},\quad N_L=\frac{m_ig}{2}-T_i,\quad N_R=\frac{m_ig}{2}+T_i
$$

$$
T_i=\frac{3433.15665\cdot0.3}{1.24}=830.602415323\ \mathrm{N},\quad{}N_L=\frac{159.075\cdot9.81}{2}-830.602415323=-50.3395403226,\quad N_R=\frac{159.075\cdot9.81}{2}+830.602415323=1610.86529032\ \mathrm{N}
$$

$$
\delta_L=\frac{N_L}{K_t},\quad\delta_R=\frac{N_R}{K_t}
$$

$$
\delta_L=\frac{-50.3395403226}{80000}=-0.000629244254032\ \mathrm{m},\quad\delta_R=\frac{1610.86529032}{80000}=0.020135816129\ \mathrm{m}
$$

$$
\phi_{\mathrm{tire}}=\frac{\delta_R-\delta_L}{t_i}
$$

$$
\phi_{\mathrm{tire}}=\frac{0.020135816129-(-0.000629244254032)}{1.24}=0.016746016438\ \mathrm{rad}=0.959476065552^\circ
$$

**接地失效：存在負輪載。** 上述負壓縮及 Roll 為線性外推參考；有效接地 Roll 為 None，不代表輪胎可承受拉力。

| 靜態單輪壓縮 m | ay 引起左側增量 m | ay 引起右側增量 m | 接地界限 g | 離地臨界 |
| --- | --- | --- | --- | --- |
| 0.0097532859375 | -0.0103825301915 | 0.0103825301915 | 2.06666666667 | 否 |

## 11.3 最小半徑轉角、方向查核與 Caster

$$
R=\frac{L}{\tan\delta},\quad \delta_{\max}=\arctan\left(\frac{L}{R_{\min}}\right)
$$

$$
\delta_{\max}=\arctan\left(\frac{1.53}{3}\right)=0.471615567862\ \mathrm{rad}=27.0215815912^\circ
$$

單軌等效前輪角取已確認的正方向。方向查核只列印比較，不修改設定；整式的座標負號固定為 −1。

| 方向驗證 Caster deg | 轉向角 deg | 原式 Camber 變化 deg |
| --- | --- | --- |
| 10 | 27.0215815912 | 3.82176691323 |
| 10 | -27.0215815912 | -5.56272988874 |

$$
\gamma_b=\phi_{\mathrm{roll}}+\phi_{\mathrm{tire}}-\Delta\gamma_{\mathrm{FVSA}}
$$

$$
\gamma_b=2.29061004264+0.944185854971-1.14530502132=2.08949087629^\circ
$$

$$
\Delta\gamma_{\mathrm{raw}}=\delta\sin C-(1-\cos\delta)\sin K,\quad{}\Delta\gamma_{\mathrm{applied}}=-\Delta\gamma_{\mathrm{raw}}
$$

$$
\sin C=\frac{\gamma_b+(1-\cos\delta)\sin K}{\delta}
$$

$$
C=\arcsin\left(\frac{\gamma_b+(1-\cos\delta)\sin K}{\delta}\right)
$$

$$
C=\arcsin\left(\frac{0.0364684954816+(1-\cos(0.471615567862))\sin(0.13962634016)}{0.471615567862}\right)=0.109761307578\ \mathrm{rad}=6.28885967803^\circ
$$

$$
\gamma_{\mathrm{final}}=\gamma_b-\Delta\gamma_{\mathrm{raw}}
$$

$$
\gamma_{\mathrm{final}}=2.08949087629-(2.08949087629)=0^\circ
$$

**Caster 算式有實數解，接地模型失效。** 本節 Camber 與 Caster 僅為線性外推參考。

---

[返回主報告](README.md) · [上一篇：懸吊剛性、自然頻率與彈簧](03_suspension_stiffness.md) · [下一篇：空力壓縮與四輪受力](05_aero_wheel_loads.md)
