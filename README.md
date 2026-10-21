# Vehicle Dynamics Toolbox

使用 CSV 參數與可點選的流程圖執行車輛動態分析。

共用的振動與阻尼模型集中在 `analysis/suspension_dynamics/`：`oscillation_models.py` 提供時間取樣、解析解、Euler 積分與能量計算；`damping_models.py` 提供阻尼參數換算與單自由度、四分之一車求解工具。各分析入口仍放在 `analysis/`，由既有流程載入。

- [共用振動與阻尼模型：計算方程式、座標與求解方法](analysis/suspension_dynamics/README.md)

所有分析共用 `ms`（全車簧上質量，kg）與 `mu`（單輪簧下質量，kg）。四分之一車模型在計算時使用 `ms / 4`；輸入框與 CSV 只保留一組質量設定。舊 CSV 的 `simulation_ms_total_kg`、`simulation_mu_kg` 會自動轉為 `ms`、`mu`；兩種名稱同時存在時，以 `ms`、`mu` 為準。

各分析結果的每張圖最多顯示四個子圖；圖片選單可切換主要結果與其他內容分組。`Time_sensitivity`、`damping_rate`、`PSD` 與 `tender` 已拆成多張圖，保留所有原有分析內容。

按「Run 全流程」或執行所選分析時，計算與存圖會在背景依序執行。Print out 會即時顯示每項分析的開始、計算輸出、儲存與完成耗時；狀態列每 0.25 秒更新目前項目與累計時間。每項結果儲存完成後就會顯示完成訊息。

分析儲存時會預先將 Markdown 的 LaTeX 公式排版為向量 HTML，雙擊結果時直接載入，避免每次重新計算公式。說明內容、介面顏色或排版程式改變時會自動更新；原有 LaTeX 與向量顯示保留。

Print out 的 `[開啟結果]` 訊息會分別顯示雙擊事件等待、圖片讀取、表格建立、說明載入及首次顯示耗時，並標示說明快取是否命中。首次顯示時間從程式開始開啟該結果起算，事件等待另列。

```powershell
.venv/Scripts/python.exe main.py
```

高低速阻尼整包分析已接在 `Damped_oscillation_analysis` 後方，依 Heave、Roll、阻尼器與 Shock Dyno、獨立懸吊等效、工況與 ODE 分成五個群組、十個小節點。

- [五類分析、流程與參數說明](analysis/hl_damping/README.md)
- [本次高低速阻尼分析報告](data/results/hl_damping/index.html)
- 流程設定：`data/analysis_flow.csv`
- 預設參數：`data/analysis_parameters.csv`

完整計算並重新產生五類本機 HTML 報告：

```powershell
.venv/Scripts/python.exe -X utf8 -m analysis.hl_damping
```

新增四輪載重與輪胎力流程：`FWL → solver_compar → sus_load → max_load`。在同一份 `data/analysis_flow.csv` 以 `flow_row=tertiary` 建立分離的「輪載與輪胎力分析」群組，與原流程之間沒有箭頭，顯示在同一張流程圖中。使用既有的「Run 全流程」與「單獨執行所選分析」操作，缺少剛性輸出時會補算必要的前置分析。

- [分離流程圖、CSV 設定與模型分析](analysis/wheel_load/README.md)
- [輪載分析結果報告](data/results/wheel_load/index.html)
- [原始 new 程式與整合版的同參數比較](data/results/wheel_load_comparison/index.html)
- 共用流程設定：`data/analysis_flow.csv`

```powershell
.venv/Scripts/python.exe -B -X utf8 -m analysis.wheel_load
```
