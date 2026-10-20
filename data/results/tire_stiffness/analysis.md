# Tire stiffness 分析

## 分析目的

依據前序 `Frequency_Stiffness` 選出的俯仰與側傾剛度，以及輪胎剛度與 motion ratio，估算彈簧剛度。所選 `Ks` 會傳給下一步 `Frequency_mass`。

## 計算方式

輪率與 ride rate 的關係為：

$$
K_w=K_s MR^2,
\qquad
K_r=\frac{K_w K_t}{K_w+K_t}
$$

分析以目標 ride rate $(K_{roll}+K_{pitch})/4$，在 20,000 至 80,000 N/m 的彈簧剛度範圍內選擇最接近的 `Ks`。另計算達到 roll 與 pitch 剛度時的彈簧剛度，並將其列為結果供檢視。
