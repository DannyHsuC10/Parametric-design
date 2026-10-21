# Brake_hydraulic_pressure：油管膨脹

CSV 已由 `new/brake_line_data.csv` 移到 `data/input_data/brake_line_data.csv`，原始油管程式也改讀此位置。資料欄位為 `type,pressure_MPa,expansion_mm3_per_m`，保留 Low／High 六筆原始數據。

分析壓力直接取 `Pedal_ratio` 輸出的前、後油路壓力中較高值，以 Pa 轉換為 MPa 後帶入油管膨脹曲線：

$$P_{target}=\frac{\max(P_{line,f},P_{line,r})}{10^6}\quad\mathrm{MPa}$$

上游數值為 `brake_pedal_front_pressure_Pa`、`brake_pedal_rear_pressure_Pa`，使用設定踏力下的計算油路壓力。輸入面板隱藏這兩個導出量，移除手動目標壓力欄位。`brake_pressure_target_MPa` 改為本節點計算輸出，另以 `brake_pressure_source_axle` 記錄取用前軸、後軸或兩側相等；載入舊參數 CSV 時不採用其中的目標壓力快照。

分別對 Low／High 進行二次曲線擬合，計算此壓力下每米管長的體積膨脹量。`brake_line_target.csv` 同時列出前後壓力、選取來源與分析壓力。目前量測範圍為 6.9～20 MPa，範圍外會在圖中與結果表標示為外插。沒有額外加入管長，因此輸出是 mm³/m，不是完整回路的膨脹體積或踏板行程；圖中的零壓力外插值也不代表物理零點。

所有節點的圖、完整資料表與本說明會儲存在 `data/results/<node_id>/`。每張圖最多四個子圖，可由既有結果圖片選單切換。
