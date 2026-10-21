# Bicycle_Model

線性二狀態 Bicycle Model 模擬定速轉向階躍，狀態為側向速度 vy 與偏航角速度 r：

$$\alpha_f=\delta-\frac{v_y+l_f r}{v_x},\qquad\alpha_r=-\frac{v_y-l_r r}{v_x}$$

$$F_{yf}=C_f\alpha_f,\qquad F_{yr}=C_r\alpha_r$$

$$\dot v_y=\frac{F_{yf}+F_{yr}}{m}-v_xr,\qquad\dot r=\frac{l_fF_{yf}-l_rF_{yr}}{I_z}$$

使用 Excel 元件分析的全車質量、全車偏航慣量、軸距及前軸配重。參考速度 `v_ref（km/h）` 可在介面手動修改，預設 40 km/h；內部以 `bicycle_v_ref_kmh` 儲存，不會被 Skidpad 的導出速度覆蓋，計算時轉為 m/s。Cf、Cr 為整軸側偏剛性，使用者確認先以各 **40,000 N/rad 示例值** 整合，可在節點參數修改。

轉向階躍角直接使用 `Turning_Radius` 的「車輛最大轉向角」輸入，該值同時標記在轉彎半徑圖上。轉向階躍開始時間固定 0.5 s、模擬時間固定 5 s、取樣固定 1000 點，直接定義在 `analysis/Bicycle_Model.py`，不提供這三項輸入框。結果包含偏航角速度、側向速度、前後輪側滑角與完整時序 CSV。終點輸出代表模擬終點，未保證已達穩態。

模型使用定速、小角度、線性輪胎假設，未加入輪胎力飽和、載荷轉移或下壓力；最大轉向角較大時，小角度近似的準確度會降低。詳細參數來源與幾何基準見 `analysis/cornering/README.md`。
