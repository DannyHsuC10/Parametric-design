# 行星齒輪與縱向性能分析

從 `new/` 整合的傳動節點接在「輪胎極限載荷」之後。流程依序為 `Acc_load → Gear_rate → Gear_tooth → Number_of_Gear → Output_check`，並由獨立的 `motor → Gear_rate` 提供馬達曲線最大扭矩；`Number_of_Gear` 另分支到 `Rotational_inertia`，`Gear_rate` 分支到 `acc_resis`，`Gear_tooth` 分支到 `tooth_Strength`。

車重、軸距、重心高度、前軸配重與輪胎摩擦係數沿用既有分析輸出或共用 CSV。原始 `new/` 程式所讀取的 `data.xlsx`／`ParameterLoader` 不在專案中，因此齒輪規格、馬達轉速及其他設定保留流程參數，可在介面或 `data/analysis_parameters.csv` 修改。這些初始值仍為可編輯示例。

`motor` 讀取正式資料 `data/input_data/motor_speed_vs_torque.csv`（從 `new/` 整合，500 點），繪製原曲線並輸出 `drive_motor_torque_Nm = max(torque)`。目前最大扭矩為 **22.30565254 N·m**。`Gear_rate`、`Output_check`、`acc_resis` 與 `tooth_Strength` 皆使用此導出量；套用前置結果時，`Gear_rate` 與 `tooth_Strength` 不顯示最大扭矩輸入框，其餘節點的扭矩欄位為唯讀，不再使用參數 CSV 的手填扭矩。勾選「全部參數手動設定」後，各節點仍可顯示並編輯專用扭矩值；馬達轉速 `drive_motor_rpm` 仍可手動設定。曲線 CSV 已納入內容變更檢查，按「執行所有受影響分析」即可先更新 motor，再依實際數值更新相關下游，略過無關流程。

`Gear_tooth` 直接以 `Gear_rate` 導出的 `gear_ratio_avg` 作為齒比搜尋目標，不另設目標齒比輸入。`Number_of_Gear` 的太陽輪、兩個行星輪及內齒輪齒數由使用者手動輸入；`Output_check` 與 `Rotational_inertia` 沿用相同齒數參數，不會覆蓋手動值。

`Gear_rate` 使用可編輯的 `acc_g`（預設 1.2 g）計算加速齒比與前後軸載荷轉移；加速需求不再由輪胎摩擦極限決定。`mu_w` 仍供 `Acc_load` 與 `Output_check` 等其他分析使用。

`Gear_tooth` 結果保留原有可行組合表格圖，並另外提供可行齒比分布與齒數組合分布兩張圖；完整候選組合也輸出 CSV。其他輸出包括動態前後軸載荷、加速與極速齒比、行星齒輪數干涉檢查、加速模擬、等效旋轉慣量、行駛阻力估算及齒根強度所需模數。每個節點輸出圖表、CSV 表格與可供下游使用的結果值。

各節點的簡要計算方程式如下，內容以現行程式為準。執行時會自動儲存為對應結果資料夾的 `analysis.md`，供結果視窗顯示 LaTeX 公式。

| 節點 | 方程式說明 |
|---|---|
| motor | [馬達曲線與最大扭矩](notes/motor.md) |
| Acc_load | [加速載重轉移](notes/acc_load.md) |
| Gear_rate | [加速與極速齒比](notes/gear_rate.md) |
| Gear_tooth | [齒數組合與搜尋條件](notes/gear_tooth.md) |
| Number_of_Gear | [行星輪數量與角度檢查](notes/number_of_gear.md) |
| Output_check | [輸出扭矩與加速模擬](notes/output_check.md) |
| Rotational_inertia | [旋轉慣量及折算](notes/rotational_inertia.md) |
| acc_resis | [行駛阻力與起步齒比](notes/acc_resis.md) |
| tooth_Strength | [齒根強度與模數](notes/tooth_strength.md) |
