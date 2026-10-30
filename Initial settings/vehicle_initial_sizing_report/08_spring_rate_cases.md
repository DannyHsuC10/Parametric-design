# 四種 Ks、Kw、Kr 比較

[返回主報告](README.md) · [上一篇：前後軸臨界阻尼](07_critical_damping.md) · [下一篇：Roll 與 Pitch gradient](09_roll_pitch_gradients.md)

## 18. 四種指定 Ks：前後 Ks → Kw → Kr、自然頻率及臨界阻尼

$$
K_s^{(1)}=\frac{K_{ht}+K_{\mathrm{roll}}}{2},\quad K_s^{(2)}=K_{ht},\quad{}K_s^{(3)}=K_{\mathrm{roll}},\quad K_s^{(4)}=K_{\mathrm{heaveonly}}
$$

Kht 為 Heave 與 Tender 的串聯值。

本節依指定除以 2，各 Ks 作單輪線性等效比較；第 7 節原 Frequency vs mass 的除以 4 模式仍另行保留。

$$
m_w=\frac{M_sw_i}{2},\quad m_{s,\mathrm{coord}}=\frac{m_w}{MR^2},\quad{}K_w=K_sMR^2,\quad K_r=\frac{K_wK_t}{K_w+K_t}
$$

$$
f_{Ks}=\frac{1}{2\pi}\sqrt{\frac{K_s}{m_{s,\mathrm{coord}}}},\quad{}f_{Kw}=\frac{1}{2\pi}\sqrt{\frac{K_w}{m_w}},\quad f_{Kr}=\frac{1}{2\pi}\sqrt{\frac{K_r}{m_w}}
$$

$$
c_{Ks}=2\sqrt{K_sm_{s,\mathrm{coord}}},\quad c_{Kw}=2\sqrt{K_wm_w},\quad c_{Kr}=2\sqrt{K_rm_w}
$$

### 前軸：(Kht + Kroll)/2

$$
K_s=\frac{K_{ht}+K_{\mathrm{roll}}}{2}
$$

$$
K_s=\frac{48311.0003349+100850.599177}{2}=74580.7997559\ \mathrm{N/m}
$$

$$
m_w=\frac{M_sw_i}{2},\quad m_{s,\mathrm{coord}}=\frac{m_w}{MR^2}
$$

$$
m_w=\frac{260.55\cdot0.5}{2}=65.1375,\quad{}m_{s,\mathrm{coord}}=\frac{65.1375}{1^2}=65.1375\ \mathrm{kg}
$$

$$
K_w=K_sMR^2,\quad K_r=\frac{K_wK_t}{K_w+K_t}
$$

$$
K_w=74580.7997559\cdot1^2=74580.7997559,\quad K_r=\frac{74580.7997559\cdot80000}{74580.7997559+80000}=38597.7041773\ \mathrm{N/m}
$$

$$
f_{Ks}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Ks}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{74580.7997559}{65.1375}}=5.38540174371\ \mathrm{Hz},\quad{}c=2\sqrt{74580.7997559\cdot65.1375}=4408.17733042\ \mathrm{N\,s/m}
$$

$$
f_{Kw}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Kw}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{74580.7997559}{65.1375}}=5.38540174371\ \mathrm{Hz},\quad{}c=2\sqrt{74580.7997559\cdot65.1375}=4408.17733042\ \mathrm{N\,s/m}
$$

$$
f_{Kr}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Kr}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{38597.7041773}{65.1375}}=3.87422933478\ \mathrm{Hz},\quad{}c=2\sqrt{38597.7041773\cdot65.1375}=3171.21929601\ \mathrm{N\,s/m}
$$

### 前軸：Kht

$$
K_s
$$

$$
K_s=48311.0003349\ \mathrm{N/m}
$$

$$
m_w=\frac{M_sw_i}{2},\quad m_{s,\mathrm{coord}}=\frac{m_w}{MR^2}
$$

$$
m_w=\frac{260.55\cdot0.5}{2}=65.1375,\quad{}m_{s,\mathrm{coord}}=\frac{65.1375}{1^2}=65.1375\ \mathrm{kg}
$$

$$
K_w=K_sMR^2,\quad K_r=\frac{K_wK_t}{K_w+K_t}
$$

$$
K_w=48311.0003349\cdot1^2=48311.0003349,\quad K_r=\frac{48311.0003349\cdot80000}{48311.0003349+80000}=30121.1900516\ \mathrm{N/m}
$$

$$
f_{Ks}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Ks}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{48311.0003349}{65.1375}}=4.33438618664\ \mathrm{Hz},\quad{}c=2\sqrt{48311.0003349\cdot65.1375}=3547.87699015\ \mathrm{N\,s/m}
$$

$$
f_{Kw}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Kw}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{48311.0003349}{65.1375}}=4.33438618664\ \mathrm{Hz},\quad{}c=2\sqrt{48311.0003349\cdot65.1375}=3547.87699015\ \mathrm{N\,s/m}
$$

$$
f_{Kr}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Kr}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{30121.1900516}{65.1375}}=3.42247789425\ \mathrm{Hz},\quad{}c=2\sqrt{30121.1900516\cdot65.1375}=2801.44178378\ \mathrm{N\,s/m}
$$

### 前軸：Kroll

$$
K_s
$$

$$
K_s=100850.599177\ \mathrm{N/m}
$$

$$
m_w=\frac{M_sw_i}{2},\quad m_{s,\mathrm{coord}}=\frac{m_w}{MR^2}
$$

$$
m_w=\frac{260.55\cdot0.5}{2}=65.1375,\quad{}m_{s,\mathrm{coord}}=\frac{65.1375}{1^2}=65.1375\ \mathrm{kg}
$$

$$
K_w=K_sMR^2,\quad K_r=\frac{K_wK_t}{K_w+K_t}
$$

$$
K_w=100850.599177\cdot1^2=100850.599177,\quad K_r=\frac{100850.599177\cdot80000}{100850.599177+80000}=44611.6737841\ \mathrm{N/m}
$$

$$
f_{Ks}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Ks}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{100850.599177}{65.1375}}=6.26244363386\ \mathrm{Hz},\quad{}c=2\sqrt{100850.599177\cdot65.1375}=5126.07292335\ \mathrm{N\,s/m}
$$

$$
f_{Kw}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Kw}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{100850.599177}{65.1375}}=6.26244363386\ \mathrm{Hz},\quad{}c=2\sqrt{100850.599177\cdot65.1375}=5126.07292335\ \mathrm{N\,s/m}
$$

$$
f_{Kr}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Kr}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{44611.6737841}{65.1375}}=4.16513274797\ \mathrm{Hz},\quad{}c=2\sqrt{44611.6737841\cdot65.1375}=3409.33594773\ \mathrm{N\,s/m}
$$

### 前軸：Kheaveonly

$$
K_s
$$

$$
K_s=141433.712574\ \mathrm{N/m}
$$

$$
m_w=\frac{M_sw_i}{2},\quad m_{s,\mathrm{coord}}=\frac{m_w}{MR^2}
$$

$$
m_w=\frac{260.55\cdot0.5}{2}=65.1375,\quad{}m_{s,\mathrm{coord}}=\frac{65.1375}{1^2}=65.1375\ \mathrm{kg}
$$

$$
K_w=K_sMR^2,\quad K_r=\frac{K_wK_t}{K_w+K_t}
$$

$$
K_w=141433.712574\cdot1^2=141433.712574,\quad K_r=\frac{141433.712574\cdot80000}{141433.712574+80000}=51097.4452552\ \mathrm{N/m}
$$

$$
f_{Ks}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Ks}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{141433.712574}{65.1375}}=7.41619361332\ \mathrm{Hz},\quad{}c=2\sqrt{141433.712574\cdot65.1375}=6070.46569969\ \mathrm{N\,s/m}
$$

$$
f_{Kw}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Kw}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{141433.712574}{65.1375}}=7.41619361332\ \mathrm{Hz},\quad{}c=2\sqrt{141433.712574\cdot65.1375}=6070.46569969\ \mathrm{N\,s/m}
$$

$$
f_{Kr}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Kr}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{51097.4452552}{65.1375}}=4.45763168847\ \mathrm{Hz},\quad{}c=2\sqrt{51097.4452552\cdot65.1375}=3648.75860551\ \mathrm{N\,s/m}
$$

### 後軸：(Kht + Kroll)/2

$$
K_s=\frac{K_{ht}+K_{\mathrm{roll}}}{2}
$$

$$
K_s=\frac{48311.0003349+82514.1265992}{2}=65412.5634671\ \mathrm{N/m}
$$

$$
m_w=\frac{M_sw_i}{2},\quad m_{s,\mathrm{coord}}=\frac{m_w}{MR^2}
$$

$$
m_w=\frac{260.55\cdot0.5}{2}=65.1375,\quad{}m_{s,\mathrm{coord}}=\frac{65.1375}{1^2}=65.1375\ \mathrm{kg}
$$

$$
K_w=K_sMR^2,\quad K_r=\frac{K_wK_t}{K_w+K_t}
$$

$$
K_w=65412.5634671\cdot1^2=65412.5634671,\quad K_r=\frac{65412.5634671\cdot80000}{65412.5634671+80000}=35987.2967823\ \mathrm{N/m}
$$

$$
f_{Ks}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Ks}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{65412.5634671}{65.1375}}=5.04353655759\ \mathrm{Hz},\quad{}c=2\sqrt{65412.5634671\cdot65.1375}=4128.3463289\ \mathrm{N\,s/m}
$$

$$
f_{Kw}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Kw}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{65412.5634671}{65.1375}}=5.04353655759\ \mathrm{Hz},\quad{}c=2\sqrt{65412.5634671\cdot65.1375}=4128.3463289\ \mathrm{N\,s/m}
$$

$$
f_{Kr}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Kr}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{35987.2967823}{65.1375}}=3.74092672242\ \mathrm{Hz},\quad{}c=2\sqrt{35987.2967823\cdot65.1375}=3062.10551363\ \mathrm{N\,s/m}
$$

### 後軸：Kht

$$
K_s
$$

$$
K_s=48311.0003349\ \mathrm{N/m}
$$

$$
m_w=\frac{M_sw_i}{2},\quad m_{s,\mathrm{coord}}=\frac{m_w}{MR^2}
$$

$$
m_w=\frac{260.55\cdot0.5}{2}=65.1375,\quad{}m_{s,\mathrm{coord}}=\frac{65.1375}{1^2}=65.1375\ \mathrm{kg}
$$

$$
K_w=K_sMR^2,\quad K_r=\frac{K_wK_t}{K_w+K_t}
$$

$$
K_w=48311.0003349\cdot1^2=48311.0003349,\quad K_r=\frac{48311.0003349\cdot80000}{48311.0003349+80000}=30121.1900516\ \mathrm{N/m}
$$

$$
f_{Ks}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Ks}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{48311.0003349}{65.1375}}=4.33438618664\ \mathrm{Hz},\quad{}c=2\sqrt{48311.0003349\cdot65.1375}=3547.87699015\ \mathrm{N\,s/m}
$$

$$
f_{Kw}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Kw}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{48311.0003349}{65.1375}}=4.33438618664\ \mathrm{Hz},\quad{}c=2\sqrt{48311.0003349\cdot65.1375}=3547.87699015\ \mathrm{N\,s/m}
$$

$$
f_{Kr}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Kr}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{30121.1900516}{65.1375}}=3.42247789425\ \mathrm{Hz},\quad{}c=2\sqrt{30121.1900516\cdot65.1375}=2801.44178378\ \mathrm{N\,s/m}
$$

### 後軸：Kroll

$$
K_s
$$

$$
K_s=82514.1265992\ \mathrm{N/m}
$$

$$
m_w=\frac{M_sw_i}{2},\quad m_{s,\mathrm{coord}}=\frac{m_w}{MR^2}
$$

$$
m_w=\frac{260.55\cdot0.5}{2}=65.1375,\quad{}m_{s,\mathrm{coord}}=\frac{65.1375}{1^2}=65.1375\ \mathrm{kg}
$$

$$
K_w=K_sMR^2,\quad K_r=\frac{K_wK_t}{K_w+K_t}
$$

$$
K_w=82514.1265992\cdot1^2=82514.1265992,\quad K_r=\frac{82514.1265992\cdot80000}{82514.1265992+80000}=40618.8081373\ \mathrm{N/m}
$$

$$
f_{Ks}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Ks}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{82514.1265992}{65.1375}}=5.66459340116\ \mathrm{Hz},\quad{}c=2\sqrt{82514.1265992\cdot65.1375}=4636.70741857\ \mathrm{N\,s/m}
$$

$$
f_{Kw}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Kw}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{82514.1265992}{65.1375}}=5.66459340116\ \mathrm{Hz},\quad{}c=2\sqrt{82514.1265992\cdot65.1375}=4636.70741857\ \mathrm{N\,s/m}
$$

$$
f_{Kr}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Kr}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{40618.8081373}{65.1375}}=3.97436890689\ \mathrm{Hz},\quad{}c=2\sqrt{40618.8081373\cdot65.1375}=3253.18773823\ \mathrm{N\,s/m}
$$

### 後軸：Kheaveonly

$$
K_s
$$

$$
K_s=141433.712574\ \mathrm{N/m}
$$

$$
m_w=\frac{M_sw_i}{2},\quad m_{s,\mathrm{coord}}=\frac{m_w}{MR^2}
$$

$$
m_w=\frac{260.55\cdot0.5}{2}=65.1375,\quad{}m_{s,\mathrm{coord}}=\frac{65.1375}{1^2}=65.1375\ \mathrm{kg}
$$

$$
K_w=K_sMR^2,\quad K_r=\frac{K_wK_t}{K_w+K_t}
$$

$$
K_w=141433.712574\cdot1^2=141433.712574,\quad K_r=\frac{141433.712574\cdot80000}{141433.712574+80000}=51097.4452552\ \mathrm{N/m}
$$

$$
f_{Ks}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Ks}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{141433.712574}{65.1375}}=7.41619361332\ \mathrm{Hz},\quad{}c=2\sqrt{141433.712574\cdot65.1375}=6070.46569969\ \mathrm{N\,s/m}
$$

$$
f_{Kw}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Kw}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{141433.712574}{65.1375}}=7.41619361332\ \mathrm{Hz},\quad{}c=2\sqrt{141433.712574\cdot65.1375}=6070.46569969\ \mathrm{N\,s/m}
$$

$$
f_{Kr}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Kr}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{51097.4452552}{65.1375}}=4.45763168847\ \mathrm{Hz},\quad{}c=2\sqrt{51097.4452552\cdot65.1375}=3648.75860551\ \mathrm{N\,s/m}
$$

| 軸別 | 案例 | Ks N/m | Kw N/m | Kr N/m | fKr Hz | cKr N·s/m |
| --- | --- | --- | --- | --- | --- | --- |
| 前軸 | (Kht + Kroll)/2 | 74580.7997559 | 74580.7997559 | 38597.7041773 | 3.87422933478 | 3171.21929601 |
| 前軸 | Kht | 48311.0003349 | 48311.0003349 | 30121.1900516 | 3.42247789425 | 2801.44178378 |
| 前軸 | Kroll | 100850.599177 | 100850.599177 | 44611.6737841 | 4.16513274797 | 3409.33594773 |
| 前軸 | Kheaveonly | 141433.712574 | 141433.712574 | 51097.4452552 | 4.45763168847 | 3648.75860551 |
| 後軸 | (Kht + Kroll)/2 | 65412.5634671 | 65412.5634671 | 35987.2967823 | 3.74092672242 | 3062.10551363 |
| 後軸 | Kht | 48311.0003349 | 48311.0003349 | 30121.1900516 | 3.42247789425 | 2801.44178378 |
| 後軸 | Kroll | 82514.1265992 | 82514.1265992 | 40618.8081373 | 3.97436890689 | 3253.18773823 |
| 後軸 | Kheaveonly | 141433.712574 | 141433.712574 | 51097.4452552 | 4.45763168847 | 3648.75860551 |

fKs = fKw 是座標一致性的結果。Kr 的臨界阻尼為 ride 等效單自由度參考，不直接代表實體阻尼器係數；Kroll 案例也不是以轉動慣量求得的整車 Roll 模態頻率。

---

[返回主報告](README.md) · [上一篇：前後軸臨界阻尼](07_critical_damping.md) · [下一篇：Roll 與 Pitch gradient](09_roll_pitch_gradients.md)
