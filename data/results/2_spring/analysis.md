# 2_spring 分析

## 分析目的

以 `Tire_Stiffness` 輸出的 pitch/heave 主彈簧剛度 `Ks_pitch_N_per_m` 為基準，串聯 tender spring，使兩者的等效剛度降至 `Frequency vs mass` 所需的目標值。分析反解 tender spring 剛度，並輸出它相對主彈簧剛度的比例。主彈簧剛度與 tender 比例會一併傳給後續 `tender` 分析。

## 輸入來源

- `Ks_pitch_N_per_m`：原 pitch/heave 主彈簧剛度（N/m），由前序 `Tire_Stiffness` 自動帶入。
- `Ks_scale_target_frequency`：達到目標自然頻率所需的剛度倍率，由前序 `Frequency vs mass` 自動帶入。

目標串聯剛度設定為：

$$
K_{series,target}=K_{s,pitch/heave}\,Ks\_scale\_target\_frequency
$$

## 串聯彈簧反算

主彈簧與 tender spring 串聯時：

$$
K_{series}=\frac{K_{s,pitch/heave}K_{tender}}{K_{s,pitch/heave}+K_{tender}}
$$

令 $K_{series}=K_{series,target}$ 並整理，可得所需 tender spring 剛度：

$$
K_{tender}=
\frac{K_{series,target}K_{s,pitch/heave}}
{K_{s,pitch/heave}-K_{series,target}}
$$

代入 $K_{series,target}=\alpha K_{heave}$，其中 $\alpha=Ks\_scale\_target\_frequency$：

$$
\frac{K_{tender}}{K_{s,pitch/heave}}=\frac{\alpha}{1-\alpha}
$$

因此分析輸出的 `tender_to_heave_stiffness_ratio` 就是所需的 $K_{tender}/K_{heave}$ 倍率；`K_tender_required_N_per_m` 為 N/m，`K_series_target_N_per_m` 為目標等效剛度。`K_heave_main_N_per_m` 是傳遞至 `tender` 的主彈簧剛度。正值、有限的 tender 剛度要求 $0<\alpha<1$。
