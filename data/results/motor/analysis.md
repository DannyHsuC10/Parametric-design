# motor：馬達轉速與扭矩曲線

資料來源為 `data/input_data/motor_speed_vs_torque.csv`，從 `new/motor_speed_vs_torque.csv` 整合。
`speed` 單位為 RPM，`torque` 單位為 N·m。曲線使用 CSV 既有資料點，不另外擬合或改動扭矩。

$$T_{m,\max}=\max_i T_i$$

`drive_motor_torque_Nm` 直接輸出 `max(torque)`，供 `Gear_rate`、`Output_check`、`acc_resis` 與
`tooth_Strength` 共用。若有多個相同最大值，最大扭矩對應轉速取其中最低轉速。

本次整合資料共有 500 點，最大扭矩為 22.30565254 N·m，對應 0 RPM。
資料範圍到 22,000 RPM；`drive_motor_rpm` 仍使用原本的可編輯轉速設定。

修改正式輸入 CSV 後，可按「執行所有受影響分析」，系統會重算 motor，再更新實際受影響的下游。
雙擊 motor 可查看曲線、最大扭矩、對應轉速與完整曲線資料表。
