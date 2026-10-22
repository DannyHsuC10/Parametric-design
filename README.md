# Vehicle Dynamics Toolbox

使用 CSV 參數與可點選的流程圖執行車輛動態分析。

流程圖上方以「選擇流程」下拉選單切換「完整流程」與各 `flow_group` 灰框群組，預設顯示完整流程。選單不另列未分組分析，這些節點仍可在完整流程中查看。群組頁面只顯示該群組的節點與內部連線，所有頁面共用參數與執行結果，並保留各自的縮放及捲動位置。流程起點（有連出去的箭頭、沒有連進來的箭頭）以淺黃色標示，工具列附有圖例。以滑鼠滾輪放大／縮小（10%～100%）、按住滑鼠左鍵或中鍵拖曳平移，也可使用水平／垂直捲軸或 Shift＋滾輪水平移動。上方提供縮放按鈕、「符合視窗」與「100%」還原原始大小。

分析方塊在滑鼠移入及按下時會變色；單擊或雙擊後，所選方塊會維持藍色高亮，切換完整流程與群組頁面時也會同步目前選取的分析。拖曳平移不會選取方塊。

單擊節點後，可選擇以下執行方式：

- **只執行所選分析**：僅重算該節點，沿用目前工作階段最近一次成功的上游結果；尚未載入的上游數值會從對應 `data/results/<node_id>/result.csv` 的導出量讀取。修改輸入參數會保留最近結果，適合上游維持不變時反覆調整下游分析。若無可用結果，會提示先執行前置分析，不會自動重跑上游。
- **所選分析＋前置分析**：重算所選節點；必要前置分析逐項比對上次成功執行的輸入與來源資料，只重算已變更或尚無成功結果的項目，其餘沿用儲存結果。修改馬達扭矩時，不會重算輸入未變更的輪胎、輪載分析。前置分析可跨群組執行。
- **執行所有受影響分析**：不需選節點，跨所有流程依序檢查並更新受參數或來源資料變更影響的分析；沒有成功結果的項目也會補算。每項分析在前置結果更新後才比較實際輸入，因此即使上游重算，只要輸出數值沒變、下游本身的輸入也沒變，下游仍會略過。單純流程先後順序不會讓無關分析跟著重算。

「Run 全流程」在任何流程頁面都會強制重算完整流程。其他三種操作也可在任何群組頁面使用。

自動比對使用各分析宣告的 `PARAMETERS` 與 `INPUT_FILES`，不是只看流程圖箭頭。來源檔案包含重心 Excel、輪胎 TIR、賽道 Excel、PSD 速度 CSV 與油管 CSV，會比對內容以偵測變更。每個節點成功儲存後寫入 `data/results/<node_id>/cache.json`；重新開啟程式或載入 CSV 後仍可沿用。既有 `result.csv` 若輸入一致且來源檔未更新，也能直接沿用。失敗、中斷、缺失或損壞的結果會在下次補算。Print out 會逐項顯示「開始」或「沿用」，最後統計重算與沿用的項目數。

流程最前方新增「輪胎模型（MF_tester）→ 最佳胎壓 → 最佳 camber → coefficient_of_friction 分析」，並由摩擦係數分支到賽道分析、Skidpad 圈速與下壓力、四輪載荷包絡（FWL）。MF_tester 輸出原 Figures 的全部 19 張圖；縱／橫向回歸摩擦係數會自動傳給後續分析。使用方式與公式見 [輪胎分析說明](analysis/tire_analysis/README.md)。

賽道分析已由 `new/` 整合至 `analysis/track_analysis/`，使用 `data/input_data/input_map.xlsx`，並在流程圖連到「懸吊壓縮行程與輪端剛性」與「路面 PSD 與速度響應」。賽道分析設定固定，不顯示輸入框；執行後雙擊開啟十一張結果圖、半徑分布與分數權重。

- [賽道分析：流程、參數、模型與輸出](analysis/track_analysis/README.md)

轉向流程為 `賽道分析 → speed_vs_R → Turning_Radius → ideal_ackemann → Bicycle_Model`；`Skidpad 圈速與下壓力` 由摩擦係數分析獨立分支。這些節點共用輪胎分析導出的橫向摩擦係數、幾何、質量與慣量；Bicycle 的 Cf／Cr 先使用各 40,000 N/rad 的可編輯示例值。

`new/Slalom.py` 已整合為 `analysis/Slalom.py`，在「轉向分析」群組新增 `Turning_Radius → Slalom` 分支。Slalom 輸入框只保留共用前輪距 `t`；賽道寬度、角錐間距、偏移比例與駕駛誤差餘裕等固定在該 Python 檔案開頭。執行後雙擊查看各組連續過彎走線圖及半徑資料。

- [彎速、轉向與 Bicycle Model：參數來源、公式與結果](analysis/cornering/README.md)

行星齒輪與縱向性能分析已由 `new/` 整合到「輪胎極限載荷」之後，包含齒比、齒數搜尋、行星齒數檢查、輸出加速模擬、旋轉慣量與阻力／齒強分析。「傳動分析」新增 `motor → Gear_rate`：`analysis/motor.py` 讀取 `data/input_data/motor_speed_vs_torque.csv`，後續馬達扭矩統一使用曲線的 `max(torque)`，目前為 22.30565254 N·m，輸入框改為唯讀。雙擊 motor 可查看曲線與資料表；修改正式曲線 CSV 後，可用「執行所有受影響分析」更新相關流程。其他齒輪規格、馬達轉速與阻力參數保留可編輯設定。

- [行星齒輪流程、參數與模型說明](analysis/gearing/README.md)

煞車分析已由 `new/` 整合到「輪胎極限載荷」之後：`輪胎極限載荷 → Brake_ratio → Pedal_ratio → Brake_force`，另由 `Pedal_ratio → Brake_hydraulic_pressure`。四個節點共用既有車重、重心、配重與輪胎參數；踏板比由上游自動計算，油管膨脹分析自動採用 `Pedal_ratio` 前後油路壓力中的較高值，資料使用 `data/input_data/brake_line_data.csv`，無須手填目標壓力。`Pedal_box` 暫不加入。新增總泵、卡鉗與碟盤規格的預設值為可編輯示例，請依實車資料調整。

- [煞車流程、參數、模型與輸出](analysis/braking/README.md)

Roll Center 分析接在「車架剛度與整車等效剛性」之後：`roll_center → roll_center_min_load_f → roll_center_same_load_r`。前軸最佳高度輸出為 `hl_front_roll_center_m`，後軸匹配高度輸出為 `hl_rear_roll_center_m`；後續 Roll 與阻尼分析會自動使用這兩個結果，不需手動輸入。

- [Roll Center 流程、參數與計算方程式](analysis/roll_center_analysis/README.md)

共用的振動與阻尼模型集中在 `analysis/suspension_dynamics/`：`oscillation_models.py` 提供時間取樣、解析解、Euler 積分與能量計算；`damping_models.py` 提供阻尼參數換算與單自由度、四分之一車求解工具。各分析入口仍放在 `analysis/`，由既有流程載入。

- [共用振動與阻尼模型：計算方程式、座標與求解方法](analysis/suspension_dynamics/README.md)

流程以 `COG_movable` 為資料起點，從 `data/input_data/Center_of_gravity_LP03_*.xlsx` 的簧上、前簧下、後簧下元件資料計算質量、重心與慣量，分出 `CG`、`Compressed travel`、`FWL 四輪載重包絡` 三條箭頭。`CG` 保留原 45°／60° 傾斜幾何比較。

所有分析共用導出量 `ms`（全車簧上質量，kg）與 `mu`（四輪平均單輪簧下質量，kg）。四分之一車模型使用 `ms / 4`；Heave／Roll 前後軸則使用各自的 `mu_front`、`mu_rear`。`hl_sprung_roll_inertia_kg_m2` 由簧上元件繞簧上重心計算；`hl_front_weight_ratio` 由全車重心與前後軸位置計算，簧上承載另用 `hl_sprung_front_weight_ratio`。

重心離地高度 `h_cog` 由使用者直接輸入，單位 m，預設 0.3 m。在 `COG_movable` 節點的「重心高度 h_cog（m）」設定後，所有下游分析共用同一值，不會加上 Excel 的 z 偏移。Excel 座標描述元件重心；前、後輪中心 x 座標需在 `COG_movable` 節點手動輸入，均以同一 Excel 原點為基準。軸距 `L` 由手動輸入的兩軸中心座標相減，前軸配重與載荷分析也使用這些座標。預設值 0.765 m、−0.765 m 是沿用原 CSV 1.53 m 軸距設定的可編輯初始值。慣量為元件集中質量近似，未含元件自身慣量。

- [重心、慣性、座標、單位與質量傳遞說明](data/results/cog_movable/analysis.md)
- [CG 傾斜幾何比較](data/results/cg/analysis.md)

各節點不顯示簧上／簧下質量、軸距 `L`、全車前軸重量比 `hl_front_weight_ratio`、簧上側傾慣量 `hl_sprung_roll_inertia_kg_m2` 的輸入框；這些值由來源資料與手動輪心座標計算，仍供下游分析使用。三份 Excel 檔案路徑固定在 `analysis/COG_movable.py`，不放在參數 CSV 中；其他質量、配重與慣量導出量可在結果表或「檢視目前變量」查閱。「所選分析＋前置分析」與「執行所有受影響分析」會偵測 Excel 內容變更並更新相關分析；「只執行所選分析」沿用最近結果。載入 CSV 時忽略其中已存的導出量，手動 `h_cog` 會保留；執行時按需讀取結果目錄中的上游快照。舊質量名稱 `simulation_ms_total_kg`、`simulation_mu_kg` 仍可由參數解析工具正規化為 `ms`、`mu`。

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

四輪載重與輪胎力流程為 `COG_movable → FWL → solver_compar → sus_load → max_load`。在同一份 `data/analysis_flow.csv` 以 `flow_row=tertiary` 建立「輪載與輪胎力分析」群組，並以 `branch_from=cog_movable` 連到共用的重心資料起點。可從下拉選單選擇完整流程或輪載群組，再選擇節點，使用「只執行所選分析」沿用上游結果，或用「所選分析＋前置分析」重算必要資料與剛性前置分析。

- [分離流程圖、CSV 設定與模型分析](analysis/wheel_load/README.md)
- [輪載分析結果報告](data/results/wheel_load/index.html)
- [原始 new 程式與整合版的同參數比較](data/results/wheel_load_comparison/index.html)
- 共用流程設定：`data/analysis_flow.csv`

```powershell
.venv/Scripts/python.exe -B -X utf8 -m analysis.wheel_load
```
