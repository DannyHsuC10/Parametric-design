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
K_s=\frac{23064.5124514+100850.599177}{2}=61957.5558141\ \mathrm{N/m}
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
K_w=61957.5558141\cdot1^2=61957.5558141,\quad K_r=\frac{61957.5558141\cdot80000}{61957.5558141+80000}=34916.1017651\ \mathrm{N/m}
$$

$$
f_{Ks}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Ks}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{61957.5558141}{65.1375}}=4.90853313395\ \mathrm{Hz},\quad{}c=2\sqrt{61957.5558141\cdot65.1375}=4017.84036111\ \mathrm{N\,s/m}
$$

$$
f_{Kw}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Kw}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{61957.5558141}{65.1375}}=4.90853313395\ \mathrm{Hz},\quad{}c=2\sqrt{61957.5558141\cdot65.1375}=4017.84036111\ \mathrm{N\,s/m}
$$

$$
f_{Kr}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Kr}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{34916.1017651}{65.1375}}=3.68483006293\ \mathrm{Hz},\quad{}c=2\sqrt{34916.1017651\cdot65.1375}=3016.18804369\ \mathrm{N\,s/m}
$$

### 前軸：Kht

$$
K_s
$$

$$
K_s=23064.5124514\ \mathrm{N/m}
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
K_w=23064.5124514\cdot1^2=23064.5124514,\quad K_r=\frac{23064.5124514\cdot80000}{23064.5124514+80000}=17902.9711801\ \mathrm{N/m}
$$

$$
f_{Ks}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Ks}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{23064.5124514}{65.1375}}=2.99486139693\ \mathrm{Hz},\quad{}c=2\sqrt{23064.5124514\cdot65.1375}=2451.41973542\ \mathrm{N\,s/m}
$$

$$
f_{Kw}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Kw}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{23064.5124514}{65.1375}}=2.99486139693\ \mathrm{Hz},\quad{}c=2\sqrt{23064.5124514\cdot65.1375}=2451.41973542\ \mathrm{N\,s/m}
$$

$$
f_{Kr}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Kr}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{17902.9711801}{65.1375}}=2.63856103579\ \mathrm{Hz},\quad{}c=2\sqrt{17902.9711801\cdot65.1375}=2159.77293737\ \mathrm{N\,s/m}
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
K_s=72829.6310738\ \mathrm{N/m}
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
K_w=72829.6310738\cdot1^2=72829.6310738,\quad K_r=\frac{72829.6310738\cdot80000}{72829.6310738+80000}=38123.3040018\ \mathrm{N/m}
$$

$$
f_{Ks}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Ks}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{72829.6310738}{65.1375}}=5.32180115638\ \mathrm{Hz},\quad{}c=2\sqrt{72829.6310738\cdot65.1375}=4356.11758063\ \mathrm{N\,s/m}
$$

$$
f_{Kw}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Kw}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{72829.6310738}{65.1375}}=5.32180115638\ \mathrm{Hz},\quad{}c=2\sqrt{72829.6310738\cdot65.1375}=4356.11758063\ \mathrm{N\,s/m}
$$

$$
f_{Kr}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Kr}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{38123.3040018}{65.1375}}=3.8503468584\ \mathrm{Hz},\quad{}c=2\sqrt{38123.3040018\cdot65.1375}=3151.67048685\ \mathrm{N\,s/m}
$$

### 後軸：(Kht + Kroll)/2

$$
K_s=\frac{K_{ht}+K_{\mathrm{roll}}}{2}
$$

$$
K_s=\frac{23064.5124514+82514.1265992}{2}=52789.3195253\ \mathrm{N/m}
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
K_w=52789.3195253\cdot1^2=52789.3195253,\quad K_r=\frac{52789.3195253\cdot80000}{52789.3195253+80000}=31803.3526877\ \mathrm{N/m}
$$

$$
f_{Ks}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Ks}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{52789.3195253}{65.1375}}=4.53082846659\ \mathrm{Hz},\quad{}c=2\sqrt{52789.3195253\cdot65.1375}=3708.67324017\ \mathrm{N\,s/m}
$$

$$
f_{Kw}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Kw}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{52789.3195253}{65.1375}}=4.53082846659\ \mathrm{Hz},\quad{}c=2\sqrt{52789.3195253\cdot65.1375}=3708.67324017\ \mathrm{N\,s/m}
$$

$$
f_{Kr}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Kr}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{31803.3526877}{65.1375}}=3.51674631669\ \mathrm{Hz},\quad{}c=2\sqrt{31803.3526877\cdot65.1375}=2878.60444361\ \mathrm{N\,s/m}
$$

### 後軸：Kht

$$
K_s
$$

$$
K_s=23064.5124514\ \mathrm{N/m}
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
K_w=23064.5124514\cdot1^2=23064.5124514,\quad K_r=\frac{23064.5124514\cdot80000}{23064.5124514+80000}=17902.9711801\ \mathrm{N/m}
$$

$$
f_{Ks}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Ks}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{23064.5124514}{65.1375}}=2.99486139693\ \mathrm{Hz},\quad{}c=2\sqrt{23064.5124514\cdot65.1375}=2451.41973542\ \mathrm{N\,s/m}
$$

$$
f_{Kw}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Kw}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{23064.5124514}{65.1375}}=2.99486139693\ \mathrm{Hz},\quad{}c=2\sqrt{23064.5124514\cdot65.1375}=2451.41973542\ \mathrm{N\,s/m}
$$

$$
f_{Kr}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Kr}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{17902.9711801}{65.1375}}=2.63856103579\ \mathrm{Hz},\quad{}c=2\sqrt{17902.9711801\cdot65.1375}=2159.77293737\ \mathrm{N\,s/m}
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
K_s=72829.6310738\ \mathrm{N/m}
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
K_w=72829.6310738\cdot1^2=72829.6310738,\quad K_r=\frac{72829.6310738\cdot80000}{72829.6310738+80000}=38123.3040018\ \mathrm{N/m}
$$

$$
f_{Ks}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Ks}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{72829.6310738}{65.1375}}=5.32180115638\ \mathrm{Hz},\quad{}c=2\sqrt{72829.6310738\cdot65.1375}=4356.11758063\ \mathrm{N\,s/m}
$$

$$
f_{Kw}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Kw}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{72829.6310738}{65.1375}}=5.32180115638\ \mathrm{Hz},\quad{}c=2\sqrt{72829.6310738\cdot65.1375}=4356.11758063\ \mathrm{N\,s/m}
$$

$$
f_{Kr}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{Kr}=2\sqrt{Km}
$$

$$
f=\frac{1}{2\pi}\sqrt{\frac{38123.3040018}{65.1375}}=3.8503468584\ \mathrm{Hz},\quad{}c=2\sqrt{38123.3040018\cdot65.1375}=3151.67048685\ \mathrm{N\,s/m}
$$

| 軸別 | 案例 | Ks N/m | Kw N/m | Kr N/m | fKr Hz | cKr N·s/m |
| --- | --- | --- | --- | --- | --- | --- |
| 前軸 | (Kht + Kroll)/2 | 61957.5558141 | 61957.5558141 | 34916.1017651 | 3.68483006293 | 3016.18804369 |
| 前軸 | Kht | 23064.5124514 | 23064.5124514 | 17902.9711801 | 2.63856103579 | 2159.77293737 |
| 前軸 | Kroll | 100850.599177 | 100850.599177 | 44611.6737841 | 4.16513274797 | 3409.33594773 |
| 前軸 | Kheaveonly | 72829.6310738 | 72829.6310738 | 38123.3040018 | 3.8503468584 | 3151.67048685 |
| 後軸 | (Kht + Kroll)/2 | 52789.3195253 | 52789.3195253 | 31803.3526877 | 3.51674631669 | 2878.60444361 |
| 後軸 | Kht | 23064.5124514 | 23064.5124514 | 17902.9711801 | 2.63856103579 | 2159.77293737 |
| 後軸 | Kroll | 82514.1265992 | 82514.1265992 | 40618.8081373 | 3.97436890689 | 3253.18773823 |
| 後軸 | Kheaveonly | 72829.6310738 | 72829.6310738 | 38123.3040018 | 3.8503468584 | 3151.67048685 |

fKs = fKw 是座標一致性的結果。Kr 的臨界阻尼為 ride 等效單自由度參考，不直接代表實體阻尼器係數；Kroll 案例也不是以轉動慣量求得的整車 Roll 模態頻率。

---

[返回主報告](README.md) · [上一篇：前後軸臨界阻尼](07_critical_damping.md) · [下一篇：Roll 與 Pitch gradient](09_roll_pitch_gradients.md)
