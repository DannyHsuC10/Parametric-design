# Roll 與 Pitch gradient

[返回主報告](README.md) · [上一篇：四種 Ks、Kw、Kr 比較](08_spring_rate_cases.md) · [下一篇：完整結果索引](10_results_index.md)

## 19. Roll 與 Pitch gradient

以整車慣性力及各固定切線剛性階段求準靜態小角度斜率，單位 deg/g；空力不增加慣性質量。

跨越 Tender 併圈點時改用相應階段，空力影響載重及所處階段。

$$
h_{\mathrm{RA}}=w_fh_{\mathrm{RC},f}+w_rh_{\mathrm{RC},r},\quad h_\phi=h-h_{\mathrm{RA}}
$$

$$
h_{\mathrm{RA}}=0.5\cdot0.0272727272727+0.5\cdot0.0330666666667=0.0301696969697\ \mathrm{m},\quad{}h_\phi=0.3-0.0301696969697=0.26983030303\ \mathrm{m}
$$

$$
K_{\phi s,i}=K_{s,i}(MRt_i)^2,\quad K_{\phi t,i}=\frac{K_tt_i^2}{2},\quad{}K_{\phi r,i}=\frac{K_{\phi s,i}K_{\phi t,i}}{K_{\phi s,i}+K_{\phi t,i}}
$$

前軸

$$
K_{\phi s,i},\quad K_{\phi t,i},\quad K_{\phi r,i}
$$

$$
K_{\phi s,i}=100850.599177(1\cdot1.25)^2=157579.061214,\quad{}K_{\phi t,i}=\frac{80000\cdot1.25^2}{2}=62500,\quad{}K_{\phi r,i}=\frac{157579.061214\cdot62500}{157579.061214+62500}=44750.6967339\ \mathrm{Nm/rad}
$$

後軸

$$
K_{\phi s,i},\quad K_{\phi t,i},\quad K_{\phi r,i}
$$

$$
K_{\phi s,i}=82514.1265992(1\cdot1.24)^2=126873.721059,\quad{}K_{\phi t,i}=\frac{80000\cdot1.24^2}{2}=61504,\quad{}K_{\phi r,i}=\frac{126873.721059\cdot61504}{126873.721059+61504}=41423.3769054\ \mathrm{Nm/rad}
$$

$$
G_{\mathrm{roll}}=\frac{Mgh_\phi}{K_{\phi,\mathrm{total}}}\frac{180}{\pi}
$$

僅懸吊

$$
G_{\mathrm{roll}}
$$

$$
G_{\mathrm{roll}}=\frac{318.15\cdot9.81\cdot0.26983030303}{284452.782273}\frac{180}{\pi}=0.169630562584\ \mathrm{deg/g}
$$

含輪胎柔度

$$
G_{\mathrm{roll}}
$$

$$
G_{\mathrm{roll}}=\frac{318.15\cdot9.81\cdot0.26983030303}{86174.0736393}\frac{180}{\pi}=0.559935064547\ \mathrm{deg/g}
$$

$$
T_{1g}=\frac{Mgh}{L},\quad{}\theta_{1g}=\frac{T_{1g}}{L}\left(\frac{1}{K_{z,f}}+\frac{1}{K_{z,r}}\right)
$$

$$
K_{\theta s}=\frac{L^2}{1/K_{z,f}+1/K_{z,r}}=\frac{K_hMR^2L^2}{2},\quad K_{\theta t}=K_tL^2
$$

$$
G_{\mathrm{pitch},s}=\frac{Mgh}{K_{\theta s}}\frac{180}{\pi},\quad{}G_{\mathrm{pitch},t}=\frac{Mgh}{K_{\theta t}}\frac{180}{\pi}
$$

$$
G_{\mathrm{pitch,total}}=G_{\mathrm{pitch},s}+G_{\mathrm{pitch},t},\quad{}G_{\mathrm{pitch,anti}}=(1-a)G_{\mathrm{pitch},s}+G_{\mathrm{pitch},t}
$$

### Pitch：Heave + Tender

$$
K_{\theta s}=\frac{K_hMR^2L^2}{2},\quad K_{\theta t}=K_tL^2
$$

$$
K_{\theta s}=\frac{48311.0003349\cdot1^2\cdot1.53^2}{2}=56545.610342,\quad{}K_{\theta t}=80000\cdot1.53^2=187272\ \mathrm{Nm/rad}
$$

$$
G_{\mathrm{pitch},s}
$$

$$
G_{\mathrm{pitch},s}=\frac{318.15\cdot9.81\cdot0.3}{56545.610342}\frac{180}{\pi}=0.948737192037\ \mathrm{deg/g}
$$

$$
G_{\mathrm{pitch},t}
$$

$$
G_{\mathrm{pitch},t}=\frac{318.15\cdot9.81\cdot0.3}{187272}\frac{180}{\pi}=0.286465267514\ \mathrm{deg/g}
$$

$$
G_{\mathrm{pitch,total}},\quad G_{\mathrm{pitch,anti}}
$$

$$
G_{\mathrm{pitch,total}}=0.948737192037+0.286465267514=1.23520245955,\quad{}G_{\mathrm{pitch,anti}}=(1-0.0909090909091)\cdot0.948737192037+0.286465267514=1.14895362391\ \mathrm{deg/g}
$$

### Pitch：純 Heave

$$
K_{\theta s}=\frac{K_hMR^2L^2}{2},\quad K_{\theta t}=K_tL^2
$$

$$
K_{\theta s}=\frac{141433.712574\cdot1^2\cdot1.53^2}{2}=165541.088882,\quad{}K_{\theta t}=80000\cdot1.53^2=187272\ \mathrm{Nm/rad}
$$

$$
G_{\mathrm{pitch},s}
$$

$$
G_{\mathrm{pitch},s}=\frac{318.15\cdot9.81\cdot0.3}{165541.088882}\frac{180}{\pi}=0.324070138358\ \mathrm{deg/g}
$$

$$
G_{\mathrm{pitch},t}
$$

$$
G_{\mathrm{pitch},t}=\frac{318.15\cdot9.81\cdot0.3}{187272}\frac{180}{\pi}=0.286465267514\ \mathrm{deg/g}
$$

$$
G_{\mathrm{pitch,total}},\quad G_{\mathrm{pitch,anti}}
$$

$$
G_{\mathrm{pitch,total}}=0.324070138358+0.286465267514=0.610535405872,\quad{}G_{\mathrm{pitch,anti}}=(1-0.0909090909091)\cdot0.324070138358+0.286465267514=0.581074484203\ \mathrm{deg/g}
$$

Anti-dive 欄為煞車方向的等效分流，只減少懸吊變形；輪胎變形保留完整負載轉移的部分。Pitch 每軸一組彈簧，與第 18 節單輪等效案例的座標及彈簧數量不同。

---

[返回主報告](README.md) · [上一篇：四種 Ks、Kw、Kr 比較](08_spring_rate_cases.md) · [下一篇：完整結果索引](10_results_index.md)
