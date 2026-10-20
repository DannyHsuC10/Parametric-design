# Frequency vs stiffness 分析

依照賽車自然頻率設定經驗大概在2~4左右，但是實際上還是需要依照動態分析為主

## 分析目的

以設定的簧載質量及前面兩項分析所需的側傾、俯仰剛度，計算固有頻率，並繪出剛度範圍內的頻率變化。

## 計算方式

沿用原始分析的四分之一車設定，使用 `ms / 2` 作為計算質量。對每個剛度 $K$ 計算：

$$
f_n = \frac{1}{2\pi}\sqrt{\frac{K}{m}}
$$

`Kr_roll` 取 `max(roll_stiffness_target_N_per_m, aero_roll_stiffness_target_N_per_m)`；俯仰剛度同理，取 `max(pitch_stiffness_target_N_per_m, aero_pitch_stiffness_target_N_per_m)`。剛度單位為 N/m。圖表顯示 10,000 至 100,000 N/m 範圍，並標出兩個選定剛度對應的頻率。
