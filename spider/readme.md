# Formula Student 資料爬取與視覺化

本專案包含 Formula Student 車輛資料、FSE 歷史成績的爬蟲，以及三個可在瀏覽器使用的視覺化工具。主要資料位於 `FSG_data_statistics/`。

在 Vehicle Initial Sizing Lab 的首頁可點 **Formula Student Data** 開啟資料區。下列命令的相對路徑以本 `spider/` 資料夾為起點，視覺化伺服器則從外層網站根目錄啟動。

## 視覺化工具

| 工具 | 頁面 | 用途 |
| --- | --- | --- |
| 車輛歷史數據分析 | `visualization/index.html` | 依年份和車隊查看車輛參數折線圖，可篩選電動車、Hoosier 與 10 吋輪胎車輛，並匯出目前篩選的資料。 |
| FSE 歷史成績分析 | `visualization/fse_results.html` | 依車隊、賽事、年份查看排名與各項成績，可匯出篩選結果。 |
| 車輛參數常態分布分析 | `visualization/vehicle_distribution.html` | 依賽事、年份及權重設定分析車輛參數分布；可勾選只統計使用 10 吋輪胎的電動車，並下載統計 CSV。界面範圍使用平均值 ± 1σ。 |

分布頁的樣本整理、平均數、標準差、權重與常態曲線公式詳見 [`visualization/車輛參數統計計算說明.md`](visualization/車輛參數統計計算說明.md)。

## 視覺化使用的 CSV

網站啟動後會自動讀取以下檔案，不需手動匯入：

| CSV | 使用頁面 | 資料內容與來源 |
| --- | --- | --- |
| `FSG_data_statistics/raw_data/FSG_EV_vehicle_database.csv` | 車輛歷史數據分析 | 車隊與年份的車輛規格。由 `FSG_data_statistics/scripts/spider_all_FSGteam.py` 爬取 Formula Student 車隊詳細頁。 |
| `FSG_data_statistics/raw_data/fse_historical_results.csv` | FSE 歷史成績分析 | 車隊、賽事、年份、名次及各項成績。由 `FSG_data_statistics/scripts/spider_fse_results.py` 爬取。 |
| `FSG_data_statistics/computed_statistics/fsg_results_vehicle_year_intersection.csv` | 車輛參數常態分布分析 | 以車隊和年份配對成績與車輛規格的交集資料。由 `extract_fsg_result_vehicle_intersections.py` 根據前兩個 CSV 產生。 |

交集檔保留歷史成績列，並附上同車隊同年份的車輛欄位（欄名以 `vehicle_` 開頭）。分布頁會在瀏覽器中再依當前篩選與權重設定計算統計結果，並使用 **±1σ** 範圍。

### 其他 CSV

- `FSG_data_statistics/raw_data/AMZ_vehicle_history.csv` 是 `spider_AMZ.py` 爬取 AMZ 單一車隊的歷史資料，目前不是上述三個視覺化頁面的預設資料來源。
- `FSG_data_statistics/computed_statistics/fsg_weighted_vehicle_parameter_ranges.csv` 是 `weighted_vehicle_parameter_ranges.py` 產生的離線統計結果。這支腳本目前輸出 **±3σ** 範圍；視覺化頁面不會讀取這個檔案。它和分布頁下載的統計 CSV 是不同流程、不同輸出。

## Python 爬蟲與資料處理

以下命令請在 `spider/` 資料夾執行。爬蟲會連線到 Formula Student 網站；若要更新資料，先執行對應爬蟲。

### 更新車輛規格

```powershell
python FSG_data_statistics/scripts/spider_all_FSGteam.py
```

輸出：`FSG_data_statistics/raw_data/FSG_EV_vehicle_database.csv`

### 更新 FSE 歷史成績

```powershell
python FSG_data_statistics/scripts/spider_fse_results.py
```

輸出：`FSG_data_statistics/raw_data/fse_historical_results.csv`

### 更新成績與車輛交集（分布頁必要）

在兩份原始 CSV 更新後執行：

```powershell
python FSG_data_statistics/scripts/extract_fsg_result_vehicle_intersections.py
```

輸出：`FSG_data_statistics/computed_statistics/fsg_results_vehicle_year_intersection.csv`

### 產生離線加權統計 CSV（選用）

```powershell
python FSG_data_statistics/scripts/weighted_vehicle_parameter_ranges.py
```

預設讀取交集 CSV，輸出 `FSG_data_statistics/computed_statistics/fsg_weighted_vehicle_parameter_ranges.csv`，目前範圍為 **±3σ**。這是離線統計檔，不會控制或更新網頁分布頁的 ±1σ 統計。

### 更新順序

若要從網站重新爬取資料並更新參數分布頁，依序執行：

```powershell
python FSG_data_statistics/scripts/spider_all_FSGteam.py
python FSG_data_statistics/scripts/spider_fse_results.py
python FSG_data_statistics/scripts/extract_fsg_result_vehicle_intersections.py
```

如果只更新車輛頁或成績頁，分別重新執行對應的車輛或成績爬蟲即可。分布頁不需要執行最後的離線加權統計腳本。

## 啟動視覺化工具

### Windows 快速啟動

1. 在 `visualization/` 資料夾雙擊 `start_visualization_server.bat`。
2. 瀏覽器會開啟車輛資料頁。伺服器執行時不要關閉命令視窗。
3. 透過頁面上方導覽切換工具，或直接開啟以下網址：

- 車輛歷史數據分析：<http://127.0.0.1:8765/spider/visualization/index.html>
- FSE 歷史成績分析：<http://127.0.0.1:8765/spider/visualization/fse_results.html>
- 車輛參數常態分布分析：<http://127.0.0.1:8765/spider/visualization/vehicle_distribution.html>

使用完畢後，在伺服器命令視窗按 `Ctrl+C` 停止。

### PowerShell 啟動

若批次檔無法啟動，在 `spider/` 的上一層（網站根目錄）開啟 PowerShell 並執行：

```powershell
python -m http.server 8765 --bind 127.0.0.1
```

接著在瀏覽器開啟上列網址。需要透過 HTTP 靜態伺服器使用，直接雙擊 HTML 檔可能無法自動讀取 CSV。

## 相關資料夾

- `FSG_data_statistics/raw_data/`：爬蟲輸出的原始 CSV。
- `FSG_data_statistics/computed_statistics/`：交集與離線統計 CSV。
- `FSG_data_statistics/scripts/`：爬蟲與資料處理程式。
