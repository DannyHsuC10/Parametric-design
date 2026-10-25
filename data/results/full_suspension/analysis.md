# Full suspension

完整懸吊模型包含四輪簧下運動、車身升沉、前後側傾、俯仰與車架扭轉。

本節點執行 road_acc 與 road_FL_bump，每個工況 1.5 秒，時間步長 0.001 秒；GIF 為 8 FPS、90 DPI。

慣量直接採用 COG_movable 既有的全車 Ixx／Iyy／Izz，與 LR／FR 模型相同；Ixx 按原始全車模型的 lr/L、lf/L 分配，Iyy、Izz 不分半。慣量輸入框隱藏，數值自動沿用 COG 前置分析結果。

Tire stiffness 的 Heave 軸設計簧率映射至主簧與輔簧串聯後的工作區剛性。運動比平方只由 KCSystem 乘一次。Heave 與前後 Roll 皆使用共用 MR，Full suspension 不讀取 hl_front_roll_motion_ratio／hl_rear_roll_motion_ratio；阻尼依實際剛性、質量及慣量換算。

Anti 比例直接共用 Tender 的 anti_geometry_ratio，套用至前後 Anti-dive／lift／squat，Full suspension 不另外顯示輸入框。輔簧／主簧剛性比直接採用 2_spring 計算的 tender_to_heave_stiffness_ratio，與 Tender 分析相同，不另設輸入框。彈簧剛性切換行程採用 Tender 的 tender_bind_total_stroke_mm，除以 1000 轉為 m，前後 Heave 共用此值，不另設輸入框。輪胎阻尼預設固定 50 N·s/m、車架扭轉阻尼固定 300 N·m·s/rad，兩者不設輸入框；高／低速阻尼切換速度固定 0.05 m/s，不設輸入框；車架扭轉剛性仍可編輯。工況 JSON 記錄輸入和實際已建立的模型係數。

road_acc 於 0.5 秒後同時施加原始縱向、橫向與垂直力；垂直力隨整車質量計算。road_FL_bump 於 0.5 至 1 秒給左前輪 5 cm 凸起，保持原始零 F_cg。沿用原始力符號與初始條件；沒有新增接地或靜態平衡假設。

原始求解器與積分公式不變。輪胎阻尼依指定預設改為 50；相同輪胎阻尼條件下，其他模型狀態與原始求解器逐通道比對一致。超出小角度模型範圍或數值發散時中止，避免產生無效結果。

完整映射與執行方式見 analysis/full_suspension/README.md。
