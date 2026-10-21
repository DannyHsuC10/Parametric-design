# Pedal_ratio：踏板比需求

固定比例曲線以回歸結果 $\beta_f$ 分配總扭矩：

$$\beta_f=\frac{1}{1+k},\qquad T_{fit,f}=\beta_f(T_f+T_r),\qquad T_{fit,r}=(1-\beta_f)(T_f+T_r)$$

其中 $k$ 由上游 `Brake_ratio` 擬合，$T_f$、$T_r$ 為各減速度下的理想前後軸扭矩。這組比例用於曲線比較；油路壓力仍依踏板比、Balance bar 與總泵規格計算。

依上述上限計算前後軸煞車力，單輪所需扭矩為 $T_i=F_{bi}R_{tire}/2$。碟盤有效半徑為 $r_e=D_{disc}/2-d_{gap}$。

本模型假設每軸兩顆相同的對向固定式卡鉗、每顆卡鉗兩側活塞對稱且等徑。兩側總活塞面積 $A_{c,i}=n_i\pi D_i^2/4$，因此單輪扭矩 $T_i=P_iA_{c,i}\mu_{pad}r_e$；不重複乘上兩側摩擦面的係數。總泵面積 $A_{m,i}=\pi D_{m,i}^2/4$，所需總泵推力 $F_{m,i}=P_iA_{m,i}$。

以 $b$ 表示前總泵推力比例，踏板比同時滿足前後回路需求：

$$PR_{required}=\frac{SF}{F_{driver}}\max\left(\frac{F_{m,f}}{b},\frac{F_{m,r}}{1-b}\right)$$

再以此踏板比與設定的車手踏力，計算前、後油路壓力：

$$P_{line,f}=\frac{F_{driver}PR_{required}b}{A_{m,f}},\qquad P_{line,r}=\frac{F_{driver}PR_{required}(1-b)}{A_{m,r}}$$

其中 $P_{req,i}=T_i/(A_{c,i}\mu_{pad}r_e)$ 是達到目標扭矩的需求油壓；$P_{line,i}$ 是設定踏力下，由踏板比與 Balance bar 產生的計算油路壓力。安全係數已含在踏板比內，不再重複乘上。此處使用理想液壓模型，忽略管路壓損。

結果圖「踏板比、前後油路壓力與扭矩需求」同時列出需求壓力與油路壓力。`pedal_line_pressure.csv` 提供前後回路的 Pa、MPa、bar 數值；$1\ \mathrm{MPa}=10^6\ \mathrm{Pa}=10\ \mathrm{bar}$。主要導出量 `brake_pedal_front_pressure_MPa`、`brake_pedal_rear_pressure_MPa` 也會顯示在主要結果表中。`pedal_sizing.csv` 原有的 `line_pressure_Pa` 欄位保留為需求油壓，新增 `pedal_line_pressure_*` 欄位記錄設定踏力下的油路壓力。

原始 `Pedal_ratio.py` 的靜態配重對調，以及扭矩曲線固定 50／50 的寫法，均改成共用前軸配重。扭矩圖明確使用整軸扭矩，需求表則提供單輪扭矩與各回路油壓。
