# 空力壓縮與四輪受力

[返回主報告](README.md) · [上一篇：Anti、Roll Center 與轉向幾何](04_geometry_steering.md) · [下一篇：傳動齒比與煞車設計](06_drivetrain_braking.md)

## 12. 下壓力造成的 Tender 壓縮

$$
F_{\mathrm{applied}}=F_{\mathrm{down}}\eta_F,\quad F_{\mathrm{assembly}}=\frac{F_{\mathrm{applied}}}{2}
$$

$$
F_{\mathrm{assembly}}
$$

$$
F_{\mathrm{assembly}}=\frac{414.616147129\cdot1}{2}=207.308073565\ \mathrm{N}
$$

$$
d_{\mathrm{main}}=\frac{F_{\mathrm{assembly}}}{K_{\mathrm{main}}/1000},\quad{}d_{\mathrm{tender}}=\frac{F_{\mathrm{assembly}}}{K_{\mathrm{tender}}/1000}
$$

$$
d_{\mathrm{main}}=\frac{207.308073565}{141.433712574}=1.4657613789\ \mathrm{mm},\quad{}d_{\mathrm{tender}}=\frac{207.308073565}{73.3741959534}=2.82535393909\ \mathrm{mm}
$$

$$
d_{\mathrm{total}}=d_{\mathrm{main}}+d_{\mathrm{tender}}
$$

$$
d_{\mathrm{total}}=1.4657613789+2.82535393909=4.29111531799\ \mathrm{mm}
$$

前後各一組相同彈簧，Heave 等於同一總壓縮量；零點為原平衡位置，只算空力增量。沿用 Tender 設計，此下壓力為併圈切換點，不把它當成任意工況下都已併圈。

## 13. 空力及 ax／ay 下的四輪受力

$$
D=F_{\mathrm{down}}\eta_F,\quad T_x=\frac{Ma_{x,g}gh}{L}
$$

$$
D=414.616147129\cdot1=414.616147129\ \mathrm{N},\quad T_x=\frac{318.15\cdot2\cdot9.81\cdot0.3}{1.53}=1223.94176471\ \mathrm{N}
$$

$$
N_f=Mgw_f+D\eta_a-T_x,\quad N_r=Mgw_r+D(1-\eta_a)+T_x
$$

$$
N_f=318.15\cdot9.81\cdot0.5+414.616147129\cdot0.5-(1223.94176471)=543.892058859\ \mathrm{N}
$$

$$
N_r=Mgw_r+D(1-\eta_a)+T_x
$$

$$
N_r=318.15\cdot9.81\cdot0.5+414.616147129(1-0.5)+(1223.94176471)=2991.77558827\ \mathrm{N}
$$

$$
K_{\phi f}=K_{s,\mathrm{roll}}(MRt_f)^2,\quad{}K_{\phi r}=K_{s,\mathrm{roll}}\frac{k_r}{k_f}(MRt_r)^2
$$

$$
\beta_f=\frac{K_{\phi f}}{K_{\phi f}+K_{\phi r}}
$$

$$
\beta_f=\frac{157579.061214}{157579.061214+126873.721059}=0.553972648658
$$

$$
T_f=\frac{\beta_f Ma_{y,g}gh}{t_f},\quad T_r=\frac{(1-\beta_f)Ma_{y,g}gh}{t_r}
$$

$$
T_f=\frac{0.553972648658\cdot318.15\cdot2.2\cdot9.81\cdot0.3}{1.25}=912.899943676,\quad{}T_r=\frac{(1-0.553972648658)\cdot318.15\cdot2.2\cdot9.81\cdot0.3}{1.24}=740.942790649\ \mathrm{N}
$$

$$
N_{FL}=\frac{N_f}{2}-T_f,\quad N_{FR}=\frac{N_f}{2}+T_f,\quad{}N_{RL}=\frac{N_r}{2}-T_r,\quad N_{RR}=\frac{N_r}{2}+T_r
$$

$$
N_{FL}
$$

$$
N=\frac{543.892058859}{2}+(-1)\cdot(912.899943676)=-640.953914247\ \mathrm{N}
$$

$$
N_{FR}
$$

$$
N=\frac{543.892058859}{2}+(1)\cdot(912.899943676)=1184.84597311\ \mathrm{N}
$$

$$
N_{RL}
$$

$$
N=\frac{2991.77558827}{2}+(-1)\cdot(740.942790649)=754.945003486\ \mathrm{N}
$$

$$
N_{RR}
$$

$$
N=\frac{2991.77558827}{2}+(1)\cdot(740.942790649)=2236.83058478\ \mathrm{N}
$$

$$
F_{x,\mathrm{total}}=Ma_{x,g}g,\quad F_{y,\mathrm{total}}=Ma_{y,g}g
$$

$$
F_{x,\mathrm{total}}=318.15\cdot2\cdot9.81=6242.103,\quad{}F_{y,\mathrm{total}}=318.15\cdot2.2\cdot9.81=6866.3133\ \mathrm{N}
$$

$$
N_i^+=\max(0,N_i),\quad q_i=\frac{N_i^+}{\sum_jN_j^+},\quad{}F_{x,i}=q_iF_{x,\mathrm{total}},\quad F_{y,i}=q_iF_{y,\mathrm{total}}
$$

**接地失效，以下三向需求力為參考。** 原始負輪載保留；截零後的總正向力與原始垂向力平衡不同。

| 輪位 | 原始 Fz N | 分配後 Fx N | 分配後 Fy N | 截零 Fz N | 合力 N | 載重占比 |
| --- | --- | --- | --- | --- | --- | --- |
| FL | -640.953914247 | 0 | 0 | 0 | 0 | 0 |
| FR | 1184.84597311 | 1770.79261182 | 1947.871873 | 1184.84597311 | 2886.82720087 | 0.283685259891 |
| RL | 754.945003486 | 1128.29098874 | 1241.12008762 | 754.945003486 | 1839.39163461 | 0.180754945688 |
| RR | 2236.83058478 | 3343.01939943 | 3677.32133938 | 2236.83058478 | 5449.94330274 | 0.535559794421 |

$$
F_{FL}=\sqrt{F_x^2+F_y^2+F_z^2}
$$

$$
F=\sqrt{(0)^2+(0)^2+(0)^2}=0\ \mathrm{N}
$$

$$
F_{FR}=\sqrt{F_x^2+F_y^2+F_z^2}
$$

$$
F=\sqrt{(1770.79261182)^2+(1947.871873)^2+(1184.84597311)^2}=2886.82720087\ \mathrm{N}
$$

$$
F_{RL}=\sqrt{F_x^2+F_y^2+F_z^2}
$$

$$
F=\sqrt{(1128.29098874)^2+(1241.12008762)^2+(754.945003486)^2}=1839.39163461\ \mathrm{N}
$$

$$
F_{RR}=\sqrt{F_x^2+F_y^2+F_z^2}
$$

$$
F=\sqrt{(3343.01939943)^2+(3677.32133938)^2+(2236.83058478)^2}=5449.94330274\ \mathrm{N}
$$

最大參考合力輪位：**RR**。

---

[返回主報告](README.md) · [上一篇：Anti、Roll Center 與轉向幾何](04_geometry_steering.md) · [下一篇：傳動齒比與煞車設計](06_drivetrain_braking.md)
