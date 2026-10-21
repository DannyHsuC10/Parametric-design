# FWL 四輪載重包絡：計算方程式

## 共用符號與單位

四輪索引固定為 $i\in\{FL,FR,RL,RR\}$。座標採 $x$ 向前、$y$ 向左、$z$ 向上；正縱向加速度使前軸卸載，正側向加速度使右側增載。

- $m_s$：全車簧上質量，對應 `ms`；$m_u$：單輪簧下質量，對應 `mu`，單位皆為 kg。
- $L$：軸距；$h$：全車重心高度；$t_f,t_r$：前、後輪距，單位皆為 m。依序對應 `L`、`h_cog`、`t`、`hl_rear_track_m`。
- $f$：前軸靜態重量比例，對應 `hl_front_weight_ratio`；後軸比例為 $1-f$。
- $D$：總下壓力，向下為正，單位 N，對應 `wl_downforce_N`；$\eta$：空力前軸分配比例，對應 `wl_aero_front_ratio`。
- $N_i$：第 $i$ 輪法向載重，向上為正，單位 N。

總質量與重力加速度為：

$$
m=m_s+4m_u,\qquad g=9.81\ \mathrm{m/s^2}
$$

CSV 的 `ax`、`ay` 是以 g 為單位的無因次輸入，以下以 $\gamma_x,\gamma_y$ 表示；代入方程式前先換算成 SI 加速度：

$$
a_x=g\gamma_x,\qquad a_y=g\gamma_y
$$

以下兩個量供四個節點共用：$W$ 為重力與下壓力的總承載，$\Delta_x$ 為前軸轉移到後軸的載重量。

$$
W=mg+D,\qquad \Delta_x=\frac{ma_xh}{L}
$$

前、後軸總載重分別為：

$$
N_f=mgf+D\eta-\Delta_x
$$

$$
N_r=mg(1-f)+D(1-\eta)+\Delta_x
$$

因此 $N_f+N_r=W$。前軸與後軸的縱向轉移量大小相等，保留正負號以涵蓋加速與煞車。下壓力視為固定工況值，作用點沒有橫向偏移。

## FWL：依重心比例求四輪載重

此方法假設橫向轉移力矩依前後靜態重量比例分配。總滾轉力矩及各軸的單側載重增減為：

$$
M_\phi=ma_yh
$$

$$
\Delta_f^{CG}=\frac{fM_\phi}{t_f},\qquad \Delta_r^{CG}=\frac{(1-f)M_\phi}{t_r}
$$

各軸左輪減載、右輪增載，得到四輪輪載：

$$
N_{FL}^{CG}=\frac{N_f}{2}-\Delta_f^{CG},\qquad N_{FR}^{CG}=\frac{N_f}{2}+\Delta_f^{CG}
$$

$$
N_{RL}^{CG}=\frac{N_r}{2}-\Delta_r^{CG},\qquad N_{RR}^{CG}=\frac{N_r}{2}+\Delta_r^{CG}
$$

各軸的左右輪載差是單側轉移量的兩倍：

$$
N_{FR}^{CG}-N_{FL}^{CG}=2\Delta_f^{CG},\qquad N_{RR}^{CG}-N_{RL}^{CG}=2\Delta_r^{CG}
$$

包絡在指定的加速度矩形範圍取樣，每個方向的點數為 `wl_grid_points`：

$$
a_x\in[-g|\gamma_x|,g|\gamma_x|],\qquad a_y\in[-g|\gamma_y|,g|\gamma_y|]
$$

各輪離地邊界與四輪非負輪載條件為：

$$
N_i(a_x,a_y)=0,\qquad \min_i N_i(a_x,a_y)\geq0
$$

輸出前、後軸輪載等高圖、三維疊圖與 `wheel_load_envelope.csv`。計算保留負輪載，以便辨認已超出四輪保持接地假設的工況。
