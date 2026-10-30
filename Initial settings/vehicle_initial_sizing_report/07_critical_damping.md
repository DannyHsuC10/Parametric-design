# 前後軸臨界阻尼

[返回主報告](README.md) · [上一篇：傳動齒比與煞車設計](06_drivetrain_braking.md) · [下一篇：四種 Ks、Kw、Kr 比較](08_spring_rate_cases.md)

## 17. Roll、Heave + Tender 與純 Heave 的前後臨界阻尼

每軸各一支 Roll 和 Heave 阻尼器；彈簧與阻尼器共用 MR。此節採固定輪端的單自由度參考。

$$
c_{\mathrm{crit}}=2\sqrt{km},\quad \zeta=\frac{c}{2\sqrt{km}}=1
$$

$$
K_\phi=K_{\phi f}+K_{\phi r},\quad C_{\phi,\mathrm{crit}}=2\sqrt{K_\phi I_{xx,s}}
$$

$$
K_\phi=157579.061214+126873.721059=284452.782273\ \mathrm{Nm/rad},\quad C_{\phi,\mathrm{crit}}=2\sqrt{284452.782273\cdot7.91782004473}=3001.49692071\ \mathrm{Nm\,s/rad}
$$

Ixx 為手動指定的簧上 CG 慣量；修改車體質量分布時需同步更新此輸入，質量改動不會自動推估新的慣量。

### 前軸 Roll

$$
K_{\phi i}=K_{s,i}(MRt_i)^2
$$

$$
K_{\phi i}=100850.599177(1\cdot1.25)^2=157579.061214\ \mathrm{Nm/rad}
$$

$$
C_{\phi i}=C_{\phi,\mathrm{crit}}\frac{K_{\phi i}}{K_\phi},\quad{}c_{\mathrm{damper},i}=\frac{C_{\phi i}}{(MRt_i)^2}
$$

$$
C_{\phi i}=3001.49692071\frac{157579.061214}{284452.782273}=1662.7471991,\quad{}c_{\mathrm{damper},i}=\frac{1662.7471991}{(1\cdot1.25)^2}=1064.15820743\ \mathrm{N\,s/m}
$$

### 後軸 Roll

$$
K_{\phi i}=K_{s,i}(MRt_i)^2
$$

$$
K_{\phi i}=82514.1265992(1\cdot1.24)^2=126873.721059\ \mathrm{Nm/rad}
$$

$$
C_{\phi i}=C_{\phi,\mathrm{crit}}\frac{K_{\phi i}}{K_\phi},\quad{}c_{\mathrm{damper},i}=\frac{C_{\phi i}}{(MRt_i)^2}
$$

$$
C_{\phi i}=3001.49692071\frac{126873.721059}{284452.782273}=1338.74972161,\quad{}c_{\mathrm{damper},i}=\frac{1338.74972161}{(1\cdot1.24)^2}=870.674896986\ \mathrm{N\,s/m}
$$

### Heave + Tender

前軸

$$
m_i=M_sw_i,\quad K_{z,i}=K_{s,i}MR^2
$$

$$
m_i=260.55\cdot0.5=130.275\ \mathrm{kg},\quad K_{z,i}=48311.0003349\cdot1^2=48311.0003349\ \mathrm{N/m}
$$

$$
c_{z,i}=2\sqrt{K_{z,i}m_i},\quad c_{d,i}=\frac{c_{z,i}}{MR^2}
$$

$$
c_{z,i}=2\sqrt{48311.0003349\cdot130.275}=5017.45575711,\quad c_{d,i}=\frac{5017.45575711}{1^2}=5017.45575711\ \mathrm{N\,s/m}
$$

後軸

$$
m_i=M_sw_i,\quad K_{z,i}=K_{s,i}MR^2
$$

$$
m_i=260.55\cdot0.5=130.275\ \mathrm{kg},\quad K_{z,i}=48311.0003349\cdot1^2=48311.0003349\ \mathrm{N/m}
$$

$$
c_{z,i}=2\sqrt{K_{z,i}m_i},\quad c_{d,i}=\frac{c_{z,i}}{MR^2}
$$

$$
c_{z,i}=2\sqrt{48311.0003349\cdot130.275}=5017.45575711,\quad c_{d,i}=\frac{5017.45575711}{1^2}=5017.45575711\ \mathrm{N\,s/m}
$$

### 純 Heave

前軸

$$
m_i=M_sw_i,\quad K_{z,i}=K_{s,i}MR^2
$$

$$
m_i=260.55\cdot0.5=130.275\ \mathrm{kg},\quad K_{z,i}=141433.712574\cdot1^2=141433.712574\ \mathrm{N/m}
$$

$$
c_{z,i}=2\sqrt{K_{z,i}m_i},\quad c_{d,i}=\frac{c_{z,i}}{MR^2}
$$

$$
c_{z,i}=2\sqrt{141433.712574\cdot130.275}=8584.93492242,\quad c_{d,i}=\frac{8584.93492242}{1^2}=8584.93492242\ \mathrm{N\,s/m}
$$

後軸

$$
m_i=M_sw_i,\quad K_{z,i}=K_{s,i}MR^2
$$

$$
m_i=260.55\cdot0.5=130.275\ \mathrm{kg},\quad K_{z,i}=141433.712574\cdot1^2=141433.712574\ \mathrm{N/m}
$$

$$
c_{z,i}=2\sqrt{K_{z,i}m_i},\quad c_{d,i}=\frac{c_{z,i}}{MR^2}
$$

$$
c_{z,i}=2\sqrt{141433.712574\cdot130.275}=8584.93492242,\quad c_{d,i}=\frac{8584.93492242}{1^2}=8584.93492242\ \mathrm{N\,s/m}
$$

---

[返回主報告](README.md) · [上一篇：傳動齒比與煞車設計](06_drivetrain_braking.md) · [下一篇：四種 Ks、Kw、Kr 比較](08_spring_rate_cases.md)
