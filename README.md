# Vehicle Initial Sizing Lab

車輛初步設計工作台，可估算重量分配、空力下壓力、懸吊剛性與自然頻率、四輪受力、齒比、煞車和阻尼。右側報告提供繁體中文與英文版本，包含公式、數值代入及重點結果。

[開啟 GitHub Pages 網頁版](https://dannyhsuc10.github.io/Parametric-design/)

## 網頁版使用方式

1. 英文網頁開啟後會載入預設參數。頂部標題列的 **Import Project** 可載入先前保存的專案 JSON，**Save Project** 可儲存目前的參數。
2. 在左側切換 **Vehicle**、**Performance**、**Suspension**、**Tires** 或 **Motors** 頁籤，調整設計參數。煞車減速度採用縱向加速度 `ax` 的輸入值。
3. 按 **Solve** 後，右側預設顯示英文報告。報告語言選單可在求解前改選 **Traditional Chinese**，也可在求解後用同一組結果切換語言。
4. 用 **Jump to section** 查看各項分析，並下載所需的報告或結果。修改參數後，重新求解即可匯出更新後的結果。

雙欄版面的右側報告可獨立捲動，結果摘要、章節選單和匯出按鈕固定在報告上方。左側欄位放不下時，可在欄位清單內捲動。手機版使用單欄版面。

首次開啟需連線至 jsDelivr 以載入 Pyodide。專案匯入、求解與檔案匯出都在瀏覽器內處理。

## 下載與匯出

| 網頁版操作 | 預設檔名 | 內容 |
| --- | --- | --- |
| Save Project | `vehicle_project.json` | 保存輸入參數，供 **Import Project** 重新載入。 |
| Download Report → Markdown | `vehicle_initial_sizing_report.md` | 保存右側目前語言的報告，包含公式、數值代入和重點結果。 |
| Download Report → CSV | `vehicle_initial_sizing_results.csv` | 完整輸入與結果，包含 `section`、`field`、`value` 三欄。採 UTF-8 BOM，無可用數值的項目留空。 |
| Download Report → Excel | `vehicle_initial_sizing_results.xlsx` | 完整輸入與結果，附分類、欄位、數值／狀態、單位和中文說明。首列凍結並可篩選，無可用數值顯示「無可用解」。布林狀態與負輪載可直接查閱。 |
| Export Dynamics JSON | `Vehicle_initial_settings.json` | 供 SuspensionDynamicsLab 使用的懸吊動態、幾何與車輛參數。 |

## 桌面版使用方式

1. 在 Windows x64 安裝 Python 3.10 以上版本（含 Tkinter）及 Microsoft Edge WebView2 Runtime，再雙擊 [Start-VehicleInitialSizingLab.bat](Start-VehicleInitialSizingLab.bat)。
2. 點左側上方的頁籤切換車輛、性能、懸吊、輪胎和馬達設定。拖曳中間的分隔線可調整輸入區寬度。煞車減速度採用 `ax` 的輸入值。
3. 按上方「儲存」或 `Ctrl+S` 保存參數專案，預設位置為本工具的 `projects/` 資料夾。按「匯入」或 `Ctrl+O` 載入 JSON，按「另存」保存另一份。
4. 按「求解」、`F5` 或 `Ctrl+Enter`，右側預設顯示英文報告。可切換報告語言或跳至指定章節。右下角可儲存目前語言的 Markdown，或匯出 CSV、Excel 和 Dynamics JSON。

### 首次建置 WebView2 檢視器

啟動檔會在檢視器尚未建置時嘗試使用 Visual Studio 隨附的 WebView2 SDK。也可在儲存庫根目錄開啟 PowerShell 手動建置。

```powershell
.\Build-WebView2Host.ps1
```

若使用由 NuGet 解壓的 `Microsoft.Web.WebView2` SDK，請加上 `-SdkRoot` 指定 SDK 資料夾。建置產物位於 `build/webview2/`。桌面報告使用隨附的 Markdown 和 LaTeX 資源，可離線顯示。

## 匯出至 SuspensionDynamicsLab

在左側懸吊頁籤（網頁版為 **Suspension**）設定目標阻尼比。求解後，網頁版按 **Export Dynamics JSON**，桌面版按「匯出json」。`Vehicle_initial_settings.json` 包含 `dynamics`（懸吊動態）、`geometry`（懸吊幾何）與 `vehicle`（車輛參數）。匯入 SuspensionDynamicsLab 後，可補填車架扭轉剛性、扭轉阻尼與傳力阻尼。舊版參數專案的目標阻尼比會在匯入時移到懸吊設定。

- 前後每輪簧下質量採同一個 `mu`，前軸驅動比例為 0.5，前軸煞車比例採理想分配擬合值。`anti_front` 與 `anti_rear` 分別採用報告的前、後軸最終 Anti 比例（1 = 100%）。
- Dynamics 匯出格式 v3 的 `heave_f_k` 與 `heave_r_k` 儲存計入輪胎柔度後的實體 Heave 主簧簧率（N/m）。SuspensionDynamicsLab 直接使用這兩個剛性值。Heave 阻尼在匯出時除以 4，對應雙輪位移總和座標。前後 Roll 採用估算值。中央 Roll 與直推的剛性和阻尼為零。
- `corner` 與 `tire` 各匯出前軸（`f`）和後軸（`r`）兩組單輪參數，每組包含剛性 `k`、阻尼 `c` 和運動比 `mr`。SuspensionDynamicsLab 對同軸左右輪使用同一組設定。
- 報告第 17 節列出 Heave、Roll 與輪胎阻尼的 LaTeX 公式與數值代入。阻尼係數使用本次求解的目標阻尼比。車架傳力虛擬質量為簧上質量的四分之一，傳力剛性為選定的線性 Roll 剛性（N/m）的十倍。
- Tender 剛性保存在 `dynamics.tender_stiffness_N_per_m`，無有效結果時為 `null`。Heave 匯出採主簧設定。
- 其餘全車欄位（例如 `Iyy`、Warp）沿用隨附的 `dynamics_template.json`。

`geometry` 在同一層列出前後 RC 高度、FVSA、KPI、Caster 和掃描設定。前軸欄位以 `_f` 標記，後軸以 `_r` 標記。前後 FVSA 採前軸計算值，前後 KPI 採同一輸入，前 Caster 採求解結果（無解時為 `null`），後 Caster 為 0°。上壓與下垂掃描皆採壓縮行程換算成 mm，靜態避讓角及轉向掃描範圍皆採計算出的前輪轉角。重力加速度與輪胎自由半徑 `R_tire` 隨 `vehicle` 匯出。完整的 GeometryLab 專案還需合併其他車輛與懸吊幾何欄位。

## 預設參數

預設值來自 [default_project.json](default_project.json) 的 `parameters`。網頁版開啟時和桌面版的「新增專案」都使用這組預設值。可直接修改 JSON，或用介面保存的參數專案更新這個檔案。Roll Center、前 Anti 與後 Anti 共用同一個車體／懸吊剛性比。

## 本機預覽與部署

### 本機預覽網頁版

在儲存庫根目錄執行下列命令，再開啟 [本機預覽](http://127.0.0.1:8000/)。Windows 也可以使用 `py -3` 代替 `python`。

```powershell
python -m http.server 8000 --bind 127.0.0.1
```

若桌面版使用 Codex 隨附的 Python，也可在 PowerShell 使用同一個執行環境。

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m http.server 8000 --bind 127.0.0.1
```

### 發布到 GitHub Pages

1. 在儲存庫的 **Settings → Pages** 將 **Source** 設為 **GitHub Actions**。
2. 將網頁、Python 模組、根目錄 JSON 或部署流程的變更推送到 `main`。也可到 **Actions → Deploy Vehicle Initial Sizing Lab**，選擇 `main` 並按 **Run workflow** 手動發布。
3. 部署完成後，從工作流程的 `github-pages` 環境連結開啟網站。工作流程會將網頁版入口、求解模組和範本打包到站點根目錄。 [部署工作流程](.github/workflows/pages.yml)

## 主要程式

- [index.html](index.html) 與 [web/workbench.css](web/workbench.css) 定義網頁版介面。
- [project.py](project.py) 定義參數欄位、驗證規則與專案格式。
- [vehicle_initial_sizing.py](vehicle_initial_sizing.py) 包含網頁版和桌面版共用的求解公式。
- [vehicle_initial_sizing_report.py](vehicle_initial_sizing_report.py) 產生報告與 CSV，[report_english.py](report_english.py) 提供英文報告文字。
- [excel_results.py](excel_results.py) 產生附欄位說明的 Excel，[dynamics_export.py](dynamics_export.py) 產生 Dynamics JSON。

Markdown 與 LaTeX 公式分別由隨附的 Marked 17.0.5 與 MathJax 3.2.2 排版。授權檔位於 [web/vendor](web/vendor/)。
