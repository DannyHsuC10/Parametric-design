# Frequency vs mass 分析

通常希望簧上下自然頻率有組構差異避免模態互相影響。

## 分析目的

以四分之一車模型估算簧載車身模態與輪胎跳動模態，並觀察兩者隨簧下質量比例的變化。分析也反推在 roll 剛度維持不變時，heave 剛度需如何調整，才能達到指定自然頻率。

## 計算方式

輸入 `ms` 為四輪簧上質量總和，`mu` 為單一車輪的簧下質量。整車總質量依 $m=ms+4\mu$ 計算，四分之一車總質量為 $m/4$。`Ks_roll_N_per_m` 是固定的 roll 彈簧剛度，`Ks_pitch_N_per_m` 是目前 pitch/heave 彈簧剛度（後續倍率所作用的剛度）。等效單側彈簧剛度、輪率及 ride rate 為：

$$
K_{s,eq}=\frac{K_{s,roll}+K_{s,heave}}{4},\qquad
K_w=K_{s,eq}MR^2,\qquad
K_r=\frac{K_wK_t}{K_w+K_t}
$$

對簧下質量比例 $r$，簧載質量為 $m_s=(m/4)(1-r)$，並計算：

$$
f_s=\frac{1}{2\pi}\sqrt{\frac{K_r}{m_s}},\qquad
f_u=\frac{1}{2\pi}\sqrt{\frac{K_t+K_w}{(m/4)r}}
$$

`MR` 為避震器位移與車輪位移的 motion ratio。質量使用 kg，剛度使用 N/m。圖表標示輸入 `mu` 對應的簧下質量比例及兩個模態頻率。

## heave 剛度倍率

`N` 是參數 CSV 中設定的大於零的浮點數，預設為 5。分析先以目前 roll 與 heave 等效剛度算出目標簧下比例下的簧下自然頻率，再用它除以 `N` 作為目標簧上 heave 模態頻率：

$$
f_{target}=\frac{f_{unsprung}}{N}
$$

在目標簧下比例下，簧載質量為 $m_s=m/4-\mu$。達到目標頻率所需的 ride rate 為：

$$
K_{r,t}=(2\pi f_{target})^2m_s
$$

考慮輪胎柔度後，反解目標輪率及等效單側彈簧剛度：

$$
K_{w,t}=\frac{K_tK_{r,t}}{K_t-K_{r,t}},\qquad
K_{s,eq,t}=\frac{K_{w,t}}{MR^2}
$$

反算時固定 roll 剛度，只調整 heave 剛度：

$$
K_{s,pitch/heave,t}=4K_{s,eq,t}-K_{s,roll},\qquad
Ks\_scale\_target\_frequency=\frac{K_{s,pitch/heave,t}}{K_{s,pitch/heave,0}}
$$

其中 $K_{s,roll}$ 固定為前序 `Tire_Stiffness` 輸出的 `Ks_roll_N_per_m`，$K_{s,pitch/heave,0}$ 是目前 `Ks_pitch_N_per_m`。因此 `Ks_scale_target_frequency` 的分母與分子都是 pitch/heave 剛度；該倍率乘在 `Ks_pitch_N_per_m` 上，roll 剛度保持不變。例如 0.8 表示 pitch/heave 剛度乘以 0.8。若 $K_{r,t}\ge K_t$ 或反算出的 pitch/heave 剛度不大於零，目標無法達成。
