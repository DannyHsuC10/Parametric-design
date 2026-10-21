# damping_rate 分析

## 分析目的與流程

接在 Time Sensitivity → Critical_Damping_Analysis 後面，掃描單自由度阻尼比，依六項正規化指標評分。後續分別接 damping_int → quarter_suspension_int，以及 damping_ode → quarter_suspension；damping_ode 同時連接 ode_spring。兩個 quarter suspension 分析最後匯合至 Damped_oscillation_analysis。結果是在固定模擬條件與候選組合下的比較，不是連續參數空間的最佳化。

## 參數與模型

簧上質量為 ms 的四分之一。Ks 自動取自 Tire stiffness，原程式的單自由度 Kr 由輪胎及 motion ratio 換算：

$$
K_w=K_sMR^2,\qquad K_r=\frac{K_wK_t}{K_w+K_t}
$$

$$
m\ddot{x}+c\dot{x}+K_rx=0,\qquad c_{critical}=2\sqrt{mK_r},\qquad c=\zeta c_{critical}
$$

本分析以固定的候選阻尼比 0.1、0.3、0.5、0.7、0.9 掃描，最低分的候選值輸出為 damping_rate_best_ratio。Critical_Damping_Analysis 圖上的標記以 Ks 為剛度；本分析則依原檔的 Kr 模型重新計算臨界阻尼，兩者的參考剛度不同。

## 最佳阻尼比自動傳遞

damping_int、damping_ode、quarter_suspension、quarter_suspension_int 均自動使用 damping_rate_best_ratio，不再手動設定阻尼比。Damped_oscillation_analysis 也讀取此值，並在比較圖中加入及加粗標示最佳候選曲線。

$$
\zeta_{used}=\zeta_{best},\qquad c=2\zeta_{best}\sqrt{mk}
$$

各模型沿用自己的質量與剛度定義：單自由度使用 Kr，四分之一車使用 Ks 與單輪簧上質量。因此共用的是最佳阻尼比，各模型的阻尼係數依各自參考臨界阻尼計算。

## Python 固定設定

於 analysis/damping_rate.py 檔案頂端設定初始位移 0.05 m、初始速度 0 m/s、模擬時間 1 s、輸出 1000 點，以及候選阻尼比、恢復容許區間、耗散比例及六項評分權重。時間與初始條件保留原檔設定。

## 指標定義

- 第一次回到平衡點：第一次穿越零位移的時間，使用相鄰取樣點線性插值。
- Overshoot：第一次穿越後的最大絕對反向位移。
- RMS：輸出位移與加速度的 RMS；評分使用加速度 RMS。
- Peak Acceleration：最大絕對加速度。
- Ride Height Recovery：進入初始位移絕對值的正負 5% 範圍，且直到模擬結束不再離開的時間。
- Energy Dissipation：輸出峰值耗散功率，並以達成 95% 初始能量耗散的時間評分。原圖標題的 90% 改成與實際計算一致的 95%。

$$
E=\frac{1}{2}mv^2+\frac{1}{2}K_rx^2,\qquad E_d=E_0-E,\qquad P=cv^2
$$

$$
x_{RMS}=\sqrt{\frac{1}{n}\sum_{i=1}^{n}x_i^2},\qquad a_{RMS}=\sqrt{\frac{1}{n}\sum_{i=1}^{n}a_i^2}
$$

## 正規化與評分

六項評分指標皆以越小越好處理；預設權重皆為 1：

$$
q_{i,j}=\frac{p_{i,j}-p_{min,j}}{p_{max,j}-p_{min,j}},\qquad Score_i=\sum_{j=1}^{6}w_jq_{i,j}
$$

如果某項指標的所有有限值相同，其有限值成本設為零。模擬時間內未發生零點穿越、恢復或 95% 耗散時，該時間指標的成本設為 1，避免原程式的 NaN 傳入 argmin 而選錯組合。圖中未達成的時間保留缺值，result.csv 以 -1 表示。

## 圖表與輸出

保留全部十個子圖，依內容拆成四張可從圖片選單切換的圖：「主要結果｜評分與最佳阻尼比」一個子圖、「位移、速度與加速度響應」三個子圖、「過零、超越量與車高恢復指標」三個子圖，以及「加速度與耗能指標」三個子圖。輸出最佳候選阻尼比、對應阻尼係數、分數，以及各候選組合的全部指標。
