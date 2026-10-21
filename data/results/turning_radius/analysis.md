# Turning_Radius

軸距 `L` 由既有元件重心分析依手動輪心座標計算，等效前輪轉角與後軸中心迴轉半徑的關係為：

$$R=\frac{L}{\tan\theta}$$

轉角掃描固定為 10–60°、500 點，直接定義在 `analysis/Turning_Radius.py`，不提供掃描參數輸入框。另提供「車輛最大轉向角」輸入框，預設 45°；紅色小點標記輸入角度的精確計算結果，並標示角度及對應轉彎半徑。

theta 為等效前輪轉角，非方向盤轉角，須大於 0° 且小於 90°；此幾何模型未加入輪胎側滑。標記超過 10–60° 時會擴展座標軸顯示，掃描曲線仍保持固定範圍。

結果附完整轉角／半徑 CSV，以及 `vehicle_turning_limit.csv` 記錄最大轉向角與對應半徑；`turning_radius_at_max_steering_m` 為該設定的導出半徑。

流程為 賽道分析 → speed_vs_R → Turning_Radius → ideal_ackemann；另由 Turning_Radius 分支至 Slalom，分析輪距與角錐配置下的連續過彎走線。詳細說明見 `analysis/cornering/README.md`。
