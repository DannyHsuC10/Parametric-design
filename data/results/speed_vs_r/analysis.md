# speed_vs_R

以共用輪胎摩擦係數 `mu_w` 計算各轉彎半徑的純摩擦極限速度：

$$v=\sqrt{\mu_w gR},\qquad g=9.81\ \mathrm{m/s^2}$$

預設掃描 3–50 m、200 點；圖表以 km/h 顯示，完整 CSV 同時保存 m/s 與 km/h。此式未含下壓力或縱向加減速。賽道時間統計共用此公式，並另加最高速度上限。

流程連到 Skidpad 圈速與下壓力、賽道分析。詳細說明見 `analysis/cornering/README.md`。
