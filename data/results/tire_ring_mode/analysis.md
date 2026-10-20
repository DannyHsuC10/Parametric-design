# Tire ring mode 分析

此分析由 `Frequency_Stiffness` 分支而出，使用 Tire_Ring_Mode 節點自己的輪胎輸入參數，不依賴該節點之前的主流程輸出。此分析可以看出需要避開的幾個輪胎模態頻率。

## 使用參數

輪胎材料密度由輸入質量與體積計算：

$$
\rho_{tire}=\frac{m_{tire}}{V_{tire}}
$$

其中 `m_tire` 為輪胎質量（kg）、`volume_tire` 為輪胎體積（m³）。

## 模態頻率

對第 $n$ 階環模態，角頻率與頻率依下式計算：

$$
\omega_n=
\sqrt{\frac{E_{tire} I_{tire}}
{\rho_{tire} A_{tire} R_{tire}^{4}}}
\,n^2(n^2-1),
\qquad
f_n=\frac{\omega_n}{2\pi}
$$

`youngs_modulus_tire` 為楊氏模數（Pa）、`second_moment_area_tire` 為截面二次矩（m⁴）、`cross_section_area_tire` 為截面積（m²），`R_tire` 為輪胎半徑（m）。第 1 階頻率固定為 0 Hz；分析階數固定為 1 至 5，圖中每個點上方標示其階數。
