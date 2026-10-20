# Compressed travel 分析

由懸吊行程限制剛性範圍，避免懸吊觸底。

## 所需俯仰與側傾剛度

以車輛質量 $m_s$、重心高度 $h$、軸距 $L$、輪距 $t$，以及以重力加速度倍數表示的縱向與側向加速度 $a_x$、$a_y$ 計算載荷轉移。本分析不套用 anti 幾何折減；anti 幾何效果只在後續 `tender` 分析中計入：

$$
F_x = \frac{m_s a_x g h}{L},
\qquad
F_y = \frac{m_s a_y g h}{t}
$$

$$
K_{pitch}(s)=\frac{F_x}{s},
\qquad
K_{roll}(s)=\frac{F_y}{s}
$$


## 懸吊行程與車身角度

由前後或左右兩端的相對位移估算車身角度：

$$
\theta_{pitch}(s)=\arctan\left(\frac{2s}{L}\right),
\qquad
\theta_{roll}(s)=\arctan\left(\frac{2s}{t}\right)
$$

圖表及導出角度使用度數表示。剛度圖中的壓縮量使用公尺，角度圖的懸吊行程使用毫米。
