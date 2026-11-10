# Vehicle Initial Sizing Lab

車輛初步設計工作台。左側設定參數，右側顯示當次求解產生的 Markdown 報告，包含表格、公式、數值代入與完整結果索引。

## 網頁版

網頁版使用 HTML/CSS 介面，並透過 Pyodide 在瀏覽器內執行與桌面版共用的 Python 求解器。首次開啟需連線至 jsDelivr 以載入 Pyodide。匯入的專案和輸入參數在瀏覽器內處理，下載專案可保存參數供下次載入。求解後可下載 Markdown、CSV 和供 SuspensionDynamicsLab 使用的 JSON。

### 本機預覽

在儲存庫根目錄執行下列命令，再開啟 [本機網頁](http://127.0.0.1:8000/)。Windows 也可以使用 `py -3` 代替 `python`。

```powershell
python -m http.server 8000 --bind 127.0.0.1
```

若桌面版使用 Codex 隨附的 Python，也可以在 PowerShell 用同一個執行環境啟動預覽。

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m http.server 8000 --bind 127.0.0.1
```

### 發布到 GitHub Pages

1. 在 GitHub 儲存庫的 **Settings → Pages** 將 **Source** 設為 **GitHub Actions**。
2. 把變更推送或合併到 `main`。如果先推送才啟用 Pages，請到 **Actions → Deploy Vehicle Initial Sizing Lab**，選 `main` 手動執行 **Run workflow**。
3. 部署完成後，在工作流程的 `github-pages` 環境連結開啟網站。工作流程會挑選網頁、求解模組及預設範本，並將網頁版 `index.html` 放在站點根目錄。

要改版面，可編輯 `index.html` 與 `web/workbench.css`。參數欄位定義在 `project.py`，預設數值在 `default_project.json`，網頁版會直接讀取這兩份檔案。

## 桌面版使用方式

1. 雙擊 `Start-VehicleInitialSizingLab.bat`，開啟獨立桌面視窗。
2. 點左側上方的頁籤切換車輛、性能、懸吊、輪胎和馬達設定。拖曳中間的分隔線可調整輸入區寬度。煞車減速度留空時沿用 `ax`。
3. 按上方「儲存」或 `Ctrl+S` 保存參數專案，預設位置為本工具的 `projects/` 資料夾。按「匯入」或 `Ctrl+O` 載入 JSON，按「另存」保存另一份。
4. 按「求解」、`F5` 或 `Ctrl+Enter`。在右側「求解報告」頁籤查看 Markdown 表格及 LaTeX 公式。用「跳至章節」查看各項分析，或按右下角「儲存 Markdown」另存當次報告。專案 JSON 保存輸入參數，載入後可重新求解。
5. 關閉桌面視窗即可結束。

「匯出 CSV」位於右下角，會輸出當次求解的輸入參數和完整結果。欄位為 `section`、`field`、`value`，無可用數值的項目留空。CSV 使用 UTF-8 BOM，可用 Excel 開啟。

## 匯出至 SuspensionDynamicsLab

在左側 **懸吊** 頁籤設定目標阻尼比。求解後，按右下角 **匯出json**，預設檔名為 `Vehicle_initial_settings.json`。匯出資料分成 `dynamics`（懸吊動態）、`geometry`（懸吊幾何）與 `vehicle`（車輛參數）。SuspensionDynamicsLab 可匯入這份 JSON，並補填車架扭轉剛性、扭轉阻尼與傳力阻尼。舊版 Initial Sizing 專案會將原阻尼比移到懸吊設定。

- 前後每輪簧下質量採同一個 `mu`，前軸驅動比例為 0.5，前軸煞車比例採理想分配擬合值。`anti_front` 與 `anti_rear` 分別採用報告的前、後軸最終 Anti 比例（1 = 100%）。
- 前後 Heave 採純主簧，簧率和阻尼係數除以 4 轉為 Dynamics 的雙輪位移總和通道。前後 Roll 採用估算值。中央 Roll 與直推的剛性和阻尼為零。
- `corner` 與 `tire` 各匯出前軸（`f`）和後軸（`r`）兩組單輪參數，每組包含剛性 `k`、阻尼 `c` 和運動比 `mr`。SuspensionDynamicsLab 對同軸左右輪使用同一組設定。
- 報告第 17 節列出 Heave、Roll 與輪胎阻尼的 LaTeX 公式與數值代入。阻尼係數使用本次求解的目標阻尼比。車架傳力虛擬質量為簧上質量的四分之一，傳力剛性為選定的線性 Roll 剛性（N/m）的十倍。
- Tender 剛性保存在 `dynamics.tender_stiffness_N_per_m`，無有效結果時為 `null`。Heave 匯出採主簧設定。
- 其餘全車欄位（例如 `Iyy`、Warp）沿用隨附的 `dynamics_template.json`。

`geometry` 在同一層列出前後 RC 高度、FVSA、KPI、Caster 和掃描設定。前軸欄位以 `_f` 標記，後軸以 `_r` 標記。前後 FVSA 採前軸計算值，前後 KPI 採同一輸入，前 Caster 採求解結果（無解時為 `null`），後 Caster 為 0°。上壓與下垂掃描皆採壓縮行程換算成 mm，靜態避讓角及轉向掃描範圍皆採計算出的前輪轉角。重力加速度與輪胎自由半徑 `R_tire` 隨 `vehicle` 匯出。完整的 GeometryLab 專案還需合併其他車輛與懸吊幾何欄位。

## 預設參數

啟動、新增專案和恢復預設時，工具會讀取 [default_project.json](default_project.json) 的 `parameters`。可直接修改 JSON 裡的數值，或在介面將一組參數另存成這個檔案。將 `brake_ax` 設為 `null` 代表求解時沿用 `ax`。

## 首次安裝

需要 Windows x64、Python 3.10+（含 Tkinter）與 Microsoft Edge WebView2 Runtime。此電腦已建置檢視器，可直接啟動。

在其他電腦首次建置時，在本資料夾開啟 PowerShell。建置腳本會先使用 Visual Studio 隨附的 WebView2 SDK。若使用從 NuGet 解壓的 `Microsoft.Web.WebView2` SDK，可用 `-SdkRoot` 指定其資料夾。

```powershell
.\Build-WebView2Host.ps1
```

工具列、參數頁籤和章節選單使用 Tkinter／ttk 的 `clam` 主題。右側的 WebView2 讀取隨附的本機資源，Markdown 排版和 LaTeX 渲染可離線完成。建置產物位於 `build/webview2/`。

求解公式見 [vehicle_initial_sizing.py](vehicle_initial_sizing.py)。報告中的模型假設、公式和數值代入由 [vehicle_initial_sizing_report.py](vehicle_initial_sizing_report.py) 產生。

Markdown 與公式分別使用隨附的 Marked 17.0.5 與 MathJax 3.2.2 排版。授權檔在 `web/vendor/`。
