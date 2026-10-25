# Roll Center 分析

流程為 `車架剛度與整車等效剛性 → roll_center → roll_center_min_load_f → roll_center_same_load_r`，在流程圖中以「Roll Center 分析」群組顯示。三支 `analysis/roll_center*.py` 為正式分析入口，原始 `new/` 程式保留。

| 節點 | 內容與方程式 |
|---|---|
| roll_center | [正規化等效剛性與解析最低點](notes/roll_center.md) |
| roll_center_min_load_f | [前軸首次轉移率峰值最小化](notes/roll_center_min_load_f.md) |
| roll_center_same_load_r | [後軸匹配前軸最佳轉移率峰值](notes/roll_center_same_load_r.md) |

各節點可單擊設定、單獨執行，並雙擊查看圖片、CSV 表格與 LaTeX 方程式。結果輸出至 `data/results/<node_id>/`；單獨執行會重算必要來源與指定前置節點。前軸最佳高度與峰值直接傳給後軸分析；前後最佳高度也分別輸出為 `hl_front_roll_center_m`、`hl_rear_roll_center_m`，供後續 Roll／阻尼分析直接使用。

質量與全車 Ixx 慣量由 `COG_movable` 導出，前軸簧上配重用於分配質量。每個軸的獨立半車模型均使用 `cog_total_Ixx_kg_m2/2`（包含簧下元件、以全車重心為基準）；前後軸不再按簧上承載比例分配慣量。線性懸吊剛性使用 `Ks_roll_N_per_m`，再套用既有前後 roll 運動比與後軸簧率比例。重心高度 `h_cog`、側向工況 `ay`（g）及前後輪距沿用共用參數。前後 Roll Center 高度分別由前軸最佳化與後軸匹配結果導出為 `hl_front_roll_center_m`、`hl_rear_roll_center_m`，直接供後續分析使用。將全車 Ixx 的一半直接作為每個軸半車模型的慣量，是本次採用的簡化假設。

Roll Center 的獨立設定包含剛性比 `rc_chassis_stiffness_ratio`（預設 10）。三個 Roll Center 節點皆提供此輸入框，並共用輸入數值；前、後軸車架等效線性剛性皆以各自懸吊等效線性剛性乘上此倍率計算。搜尋與模擬設定固定在程式中：RC／重心高度比 0.01～0.99、50 個掃描點、時間間隔 0.001 s、總模擬時間 2 s。

原始 `data.xlsx`／`ParameterLoader` 未隨專案提供，因此使用上述共用來源。線性動態保留原本的懸吊與車架兩條無阻尼路徑，將角度透過輪距轉為位移，使剛性與力的單位一致，並使用解析階躍解。額外細分首次脈衝的時間點以避免粗取樣漏掉峰值；不依賴原始程式對可能不存在的脈衝作插值。

第一節點的正規化等效剛性與後兩節點的轉移率目標是不同指標。後兩者最佳化的單位是 N/s，沒有將峰值轉移率當成峰值輪載或完整車輛側傾最佳化；目前未包含阻尼、輪胎動態、輪胎離地與前後軸車架耦合。`overall_rigidity` 為使用者指定的前置流程，車架比值仍使用本套件的可編輯參數。
