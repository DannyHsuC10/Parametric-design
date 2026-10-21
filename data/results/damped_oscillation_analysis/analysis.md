# Damped oscillation analysis

## 分析目的與流程

由 quarter_suspension_int 與 quarter_suspension 兩路匯合進入本分析，掃描不同阻尼比對簧上位移及動態輪胎負載的影響，並標示 damping_rate 選出的最佳候選阻尼比。

此節點後延伸為五個高低速阻尼分析群組：Heave、Roll、阻尼器與 Shock Dyno、獨立懸吊等效、工況與 ODE。Heave 與 Roll 先分支建立模型，再匯合進入阻尼器定尺寸及單輪等效設定，最後比較準靜態與暫態工況。各群組分成兩個可點選的小節點，完整說明見 analysis/hl_damping/README.md。

新的 Heave／Roll 目標阻尼比分別由 hl_*_zeta 參數設定；本節點掃描得到的 quarter-car 最佳阻尼比保留作為設計參考，並未直接覆寫新的三自由度目標。

## 參數來源

使用 ms 的四分之一作為簧上質量，mu 作為單輪簧下質量；懸吊彈簧剛度 Ks 自動取自 Tire stiffness，輪胎剛度使用 CSV 的 Kt。

$$
c_{ref}=2\sqrt{m_sK_s},\qquad c_s=\zeta c_{ref}
$$

本分析自動讀取 damping_rate_best_ratio，將最佳候選阻尼比加入原有 0、0.2、0.4、0.7、1.0 的比較組合；若數值重複則僅計算一次。最佳候選曲線加粗並以 damping_rate best 標示。最佳阻尼比不提供輸入框，也不在 CSV 手動設定。這裡的阻尼比以簧上單自由度公式作為參考尺度。

## 運動方程式與負載

平坦路面上的自由振動方程式為：

$$
m_s\ddot{x}_s=-K_s(x_s-x_u)-c_s(\dot{x}_s-\dot{x}_u)
$$

$$
m_u\ddot{x}_u=K_s(x_s-x_u)+c_s(\dot{x}_s-\dot{x}_u)-K_tx_u
$$

沿用原始程式的帶正負號輪胎負載變化定義：

$$
F_{z,static}=(m_s+m_u)g,\qquad \Delta F_z=K_tx_u,\qquad F_z=F_{z,static}+\Delta F_z
$$

圖表比較帶正負號的變化；輸出另列最大絕對變化。本線性模型未加入輪胎離地後的接觸切換。

## Python 固定設定

於 analysis/Damped_oscillation_analysis.py 檔案頂端設定阻尼比組合、初始狀態 (0.05 m, 0 m/s, 0 m, 0 m/s)、模擬時間 3 s、輸出 1000 點，保留原程式的預設 RK45 容許誤差。

## 圖表與輸出

同圖兩個面板分別為簧上位移與輪胎負載變化。輸出使用的 Ks、參考臨界阻尼、靜態輪胎負載，以及原有各比較阻尼比的最大絕對簧上位移與輪胎負載變化。另以 damped_sweep_selected_ratio_used、damped_sweep_selected_coefficient_Ns_per_m 及 selected_peak 輸出記錄最佳候選組合的阻尼比、阻尼係數與峰值。
