# Steady_lapsim 圈速結果分析

輸入：`data/input_data/steady_lapsim.pkl`（由 `new/data.pkl` 搬入）。
原畫圖工具整理在 `analysis/steady_lapsim/plot_track_speed_map.py`，桌面分析入口為 `analysis/Steady_lapsim.py`，不新增參數輸入框。

流程圖加入 `Brake_force → Steady_lapsim`、`Output_check → Steady_lapsim`、`aero 3D → Steady_lapsim`，位於「圈速模擬」群組。這三條箭頭表示模擬的工程輸入關係；本節點只讀取已匯出的記錄，不使用目前上游數值重算圈速。上游參數改變後，需在原模擬器重跑並替換 PKL；「執行所有受影響分析」會偵測 PKL 內容變更並重新產圖。

## 圖表與計算

- 賽道速度彩圖：直接使用 `s_world` 記錄的 X、Y 座標與 `v[:, 0]` 車速（m/s）。
- 速度／路程圖：依 accelerate、brake、hold 三個階段標色。
- 階段摘要圖與表格：以相鄰樣本的時間差與路程差加總，占比依時間或路程加權，不以樣本數代替。區間歸屬其起點的 phase，最後一點不另算區間。
- 圈速為 `t[-1] - t[0]`，路程為 `s[-1, 0] - s[0, 0]`；平均速度為路程／圈速。若 metadata 圈速與時間跨度不同，會報錯以免混用記錄。

結果儲存在 `data/results/steady_lapsim/`：`plot.png`、`phase_summary.png`、`lap_samples.csv`、`phase_summary.csv`、`result.csv` 與本次 `analysis.md`。桌面程式雙擊節點可切換兩張圖與結果表。

## 記錄的適用範圍

本次資料來源為 `theoretical_lap_simulator.py` 的簡化穩態速度規劃。前後 roll 設為相同以計算空力姿態，動態懸吊欄位為運動學估計，不能視為完整暫態懸吊模擬。
PKL 未存原橫向極限速度曲線，因此不補畫。metadata 中的賽道與輪胎路徑保留為來源資訊；畫圖不依賴原模擬器的絕對路徑，也不以其他賽道猜測邊界。只載入可信來源的 pickle。

只畫原速度圖：

```powershell
.venv/Scripts/python.exe -m analysis.steady_lapsim.plot_track_speed_map --no-show
```

產生完整分析：

```powershell
.venv/Scripts/python.exe -m analysis.steady_lapsim
```
