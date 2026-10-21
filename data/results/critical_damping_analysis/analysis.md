# Critical Damping Analysis

## 分析目的與流程

本分析直接接在 Time Sensitivity 後面，後續接 damping_rate，再分往 damping_int 與 damping_ode。

本分析依原始程式建立剛度掃描的自然頻率與臨界阻尼曲線，使用共用質量及 Tire stiffness 的 Ks 標記參考值。damping_rate 依其單自由度 Kr 模型計算臨界阻尼並選出最佳候選阻尼比，後續有阻尼分析自動使用該阻尼比。

## 質量與剛度來源

ms 為四輪簧上總質量，分析時除以 4。原始檔的 param.m 改用這個共用質量設定。Ks 自動取自 Tire stiffness，標記在兩張曲線上，不提供輸入框。

$$
m=\frac{m_{s,total}}{4},\qquad \omega_n=\sqrt{\frac{k}{m}},\qquad f_n=\frac{1}{2\pi}\sqrt{\frac{k}{m}}
$$

$$
c_{critical}=2\sqrt{km}
$$

以上為單自由度公式，也可作為二自由度簧上系統的阻尼參考尺度；不代表整個二自由度系統的每個模態都臨界阻尼。

## Python 固定設定

於 analysis/Critical_Damping_Analysis.py 檔案頂端設定剛度掃描範圍 10,000 至 300,000 N/m，共 1000 點，保留原檔設定。

## 圖表與輸出

上圖顯示自然頻率，下圖顯示臨界阻尼；兩圖皆以紅色點與垂直虛線標示目前的 Ks。輸出四分之一簧上質量、標記的 Ks、該點的自然頻率與臨界阻尼係數。
