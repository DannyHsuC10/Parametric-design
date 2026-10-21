# 輪胎模型（MF_tester）

執行 `analysis/Pacejka_tire_model/MF_tester.py` 的完整圖表生成流程，保留原始 Figures 內 19 張圖的檔名。包含 FX、FY、MX、MZ、RRT 在固定側滑角、滑移率、載荷下的 15 張曲面，以及四張摩擦圓圖。

固定讀取 `data/input_data/tire.tir`，展示胎壓固定為 82319 Pa、camber 固定為 0°，不顯示輸入框。主圖是 FY 固定滑移率曲面，其他圖可從圖片選單選取。圖表採用原模型公式，以 NumPy 網格計算。

完整分析方法及流程見 [輪胎分析說明](../../../analysis/tire_analysis/README.md)。
