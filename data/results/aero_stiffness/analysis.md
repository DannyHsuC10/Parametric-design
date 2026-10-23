# 傾斜角 stiffness 分析

根據空力敏感度限制車輛傾角，其中雖然roll敏感度較低而且還有roll center 可以分掉一部份的LLT，但是輪胎傾斜會造成camber變化，還是不能放太寬。前懸吊幾何有機會補camber gain 1 deg ，輪胎在正負 1 deg 內也不會有太大的性能衰退，如果空力對於roll不敏感可以用這幾個面向設定roll 允許角度

## 分析目的

依據車輛質量、縱向與側向加速度、重心高度、軸距及輪距，估算指定俯仰角與側傾角所需的剛度。加速度 `ax` 與 `ay` 以重力加速度 $g$ 的倍數輸入。

## 俯仰剛度

在俯仰角 $\theta$ 下，前後軸間的半軸距位移為：

$$
s_{pitch}=\frac{L}{2}\theta
$$

縱向加速度造成的俯仰力矩與等效力為：

$$
M_{pitch}=m_s a_x g h_{cog},
\qquad
F_{pitch}=\frac{M_{pitch}}{L/2}
$$

所需俯仰剛度：

$$
K_{pitch}=\frac{F_{pitch}}{2s_{pitch}}
$$

## 側傾剛度

在側傾角 $\phi$ 下，左右輪距半幅的位移與側傾剛度為：

$$
s_{roll}=\frac{t}{2}\phi,
\qquad
M_{roll}=m_s a_y g h_{cog},
\qquad
F_{roll}=\frac{M_{roll}}{t/2},
\qquad
K_{roll}=\frac{F_{roll}}{2s_{roll}}
$$

角度以度數設定並轉為弧度計算。分析在 $0.1^\circ$ 到 $3.0^\circ$ 範圍以 $0.1^\circ$ 間距取樣，輸出最接近目標角度的剛度及位移。結果圖以剛度為橫軸、角度為縱軸，並標示所選取樣點。
