# DXF 轉換成圖資說明

## 目的

本文件說明 `DXF_to_lapdata.py` 如何將 DXF 中的 `LINE` 和 `ARC` 幾何資料轉成我們可用的賽道圖資格式，並儲存為 `input_map.xlsx`。

## 整體流程

1. 讀取 DXF 檔案並分析圖形元素。
2. 解析 `LINE` 與 `ARC` 實體，將它們轉成段落資料。
3. 將段落排序成連續賽道路徑。
4. 讀取 `input_map_tmp.xlsx` 範本檔案，並複製成 `input_map.xlsx`。
5. 將解析後的段落寫入 `Shape` 工作表。
6. 在 `Info` 工作表第 1 列寫入 `Name` 與 DXF 檔案名稱。

## 讀取與解析 DXF 元素

程式會遍歷 DXF 模型空間 `msp`，並針對每個 entity 執行以下處理：

- `LINE`
  - 取出起點 $P_0=(x_0,y_0)$ 與終點 $P_1=(x_1,y_1)$。
  - 計算線段長度：

$$
L = \sqrt{(x_1 - x_0)^2 + (y_1 - y_0)^2}
$$

- `ARC`
  - 取出圓心 $(c_x,c_y)$、半徑 $R$、起始角度 $\theta_0$ 以及終止角度 $\theta_1$。
  - 以弧角 $\Delta\theta$ 估算弧長：

$$
\Delta\theta = \operatorname{mod}(\theta_1 - \theta_0, 2\pi)
$$

$$
L = R\,|\Delta\theta|
$$

  - 計算對應的起點與終點座標：

$$
P_0 = (c_x + R\cos\theta_0,\ c_y + R\sin\theta_0)
$$

$$
P_1 = (c_x + R\cos\theta_1,\ c_y + R\sin\theta_1)
$$

  - 在程式中，若 `end_angle` 小於 `start_angle`，會加上 $2\pi$ 來處理跨過 $360^\circ$ 的情況。

## 連續段落排序

為了把 DXF 檔案的分段轉成連續的賽道路徑，程式會將段落排序。

- 以上一段的終點 `last.end` 為基準。
- 如果下一段的起點接近 `last.end`，則認為它是相連段。
- 若下一段的終點接近 `last.end`，則反轉該段的方向。

這裡使用容差判斷：

$$
\sqrt{(x_a - x_b)^2 + (y_a - y_b)^2} < \text{tol}
$$

其中 $\text{tol}$ 預設為 $10^{-8}$，用來避免浮點數誤差造成錯誤分段。

## 轉換成 Excel 圖資

轉換後的段落資料會寫入 Excel 的 `Shape` 工作表。每筆資料包含：

- `section`
- `Type`（`LINE` 或 `ARC`）
- `Start_X`, `Start_Y`
- `End_X`, `End_Y`
- `Center_X`, `Center_Y`（僅 `ARC` 使用）
- `Radius`（僅 `ARC` 使用）
- `Start_Angle (deg)`, `End_Angle (deg)`
- `length`
- `Direction`

這樣的格式與後續的 `opentrack.py` 解析方式相容。

## 使用 `input_map_tmp.xlsx` 範本

程式會先讀取 `input_map_tmp.xlsx`，作為輸出檔的範本。這樣可以保留範本中的其他工作表與樣板資料。

- 若 `input_map_tmp.xlsx` 存在，則載入它。
- 若範本不存在，則建立新 Workbook。
- 複製內容後另存為 `input_map.xlsx`。

## 更新 `Info` 工作表

在 `Info` 工作表第 1 列寫入：

- A1：`Name`
- B1：DXF 檔案名稱

這可以讓後續讀取工具知道此圖資來源是哪一個 DXF 檔案。

## 數學與力學概念

### 幾何重建

DXF 中的 `LINE` 與 `ARC` 分別代表直線段與圓弧段。在賽道動力學中，這兩種段落可以用以下方式處理：

- 直線段的曲率 $\kappa = 0$。
- 圓弧段的曲率為：

$$
\kappa = \frac{s}{R}
$$

其中 $s$ 為方向符號，$s=+1$ 代表左彎，$s=-1$ 代表右彎。

### 曲率與車輛力學

曲率 $\kappa$ 與瞬時轉彎半徑 $\rho$ 的關係為：

$$
\rho = \frac{1}{|\kappa|}
$$

對車輛而言，側向加速度 $a_y$ 與速度 $v$ 和半徑 $\rho$ 的關係為：

$$
a_y = \frac{v^2}{\rho}
$$

因此，DXF 轉換成的圓弧段資料可直接用於賽道速度評估與輪胎負載分析。

### 連續段落的物理意義

段落排序是確保賽道連續性的關鍵。若段落斷裂，則半徑、曲率與賽道總長度的分析將失去正確性。

段落接續時，應滿足：

$$
P_{\text{end}}^{(k)} \approx P_{\text{start}}^{(k+1)}
$$

若不相等，代表路徑不連續，可能造成賽道解析失敗。

## 產出結果

輸出檔案：

- `input_map.xlsx`

主要變化：

- `Shape` 工作表改寫為 DXF 解析後的段落資料。
- `Info` 工作表第 1 列寫入 `Name` 與 DXF 檔案名稱。

## 使用方式

1. 將 DXF 檔案放置於 `track` 資料夾。
2. 確保 `input_map_tmp.xlsx` 在 `output_lapsim` 子資料夾或程式預設路徑可讀取。
3. 執行 `DXF_to_lapdata.py`。
4. 檢查 `input_map.xlsx` 是否已在 `track` 資料夾中生成。

## 注意事項

- 如果 DXF 中的 `ARC` 起點與終點角度跨越 $360^\circ$，程式會自動補 $2\pi$，以維持弧段連續性。
- 目前程式的排序依賴精準點對齊，因此若 DXF 中有微小誤差，可能需要調整容差 `tol`。
- `LINE` 與 `ARC` 的方向判斷會影響 `Direction` 欄位值（`Clockwise` 或 `Counterclockwise`）。
