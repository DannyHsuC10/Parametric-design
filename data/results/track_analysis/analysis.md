# 賽道分析

從 `data/input_data/input_map.xlsx` 重建賽道中心線，分析曲率、Apex、半徑分布與分數權重。圖片選單提供十一張圖，包含賽道平面、曲率與 Apex、空間頻率／波長頻譜、半徑時間／距離／分數分布，以及高程、坡度、Banking、Grip Factor。

彎道速度估算：

$$
v(R)=\min\left(\sqrt{\mu_w gR},\frac{v_{\max,\mathrm{km/h}}}{3.6}\right),\qquad
\Delta t=\frac{\Delta x}{v(R)},\qquad g=9.81\ \mathrm{m/s^2}
$$

時間與距離依 1 m 半徑區間累計，只包含設定半徑上限內的彎道。直線不在這些分布中；`track_corner_time_s` 為彎道累計時間。此估算未加入縱向加減速、下壓力、坡度、Banking 或 Grip Factor 的速度修正。

Autocross 與 Endurance 分數按各半徑區間的彎道時間占比分配；Skidpad 分數加在最接近 9.125 m 的非空區間。分數預設沿用原程式的 75／100／250 分，可在節點參數中修改。`track_top_5_score_rate_percent` 表示前五名半徑區間占總分數池的百分比。

流程由賽道分析連到 speed_vs_R，再延伸 Turning_Radius → ideal_ackemann → Bicycle_Model；賽道分析仍連到 Skidpad 圈速與下壓力、懸吊壓縮行程與輪端剛性及路面 PSD 與速度響應。下游模型沿用各自的輸入；PSD 速度資料仍來自 `vt_data.csv`。曲率 FFT 使用空間頻率（1/m），PSD 激振頻率使用 Hz。

完整說明見 `analysis/track_analysis/README.md`。結果另附三張半徑分布 CSV、`OpenTRACK.npz`、`track.json` 與 `OpenTRACK.log`。
