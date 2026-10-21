# roll_center_same_load_r：後軸匹配前軸轉移率峰值

以前一節點的前軸最佳高度及最低峰值 $R_f^{*}$ 為基準，掃描後軸 RC，找出前後峰值最接近的組合。後軸車架路徑採 $m_r/4$ 等效質量。

$$m_r=m_s(1-f_s),\qquad I_r=\frac{I_{xx,total}}{2}$$

其中 $I_{xx,total}$ 是 `cog_total_Ixx_kg_m2`，包含簧下元件並以全車重心為基準；後軸獨立半車模型直接使用其一半，後軸簧上承載比例僅用於分配質量。

$$k_{s,r}=K_{s,roll}\gamma_rMR_r^2,\qquad k_{c,r}=ck_{s,r}$$

$\gamma_r$ 沿用 `hl_rear_roll_spring_ratio`，$MR_r$ 使用 `hl_rear_roll_motion_ratio`，輪距使用 `hl_rear_track_m`。其餘運動方程式與前軸相同。

$$R_r^{peak}(h_{rc,r})=\max_{\tau}|R_{s,r}(\tau)+R_{c,r}(\tau)|$$

$$h_{rc,r}^{*}=\mathrm{argmin}_{h_{rc,r}}\left|R_r^{peak}(h_{rc,r})-R_f^{*}\right|$$

$$\varepsilon=\left|R_r^{peak}(h_{rc,r}^{*})-R_f^{*}\right|$$

顯示後軸峰值曲線、前軸參考線、最佳匹配點及前後首次脈衝。搜尋範圍固定為 1%～99% 重心高度，共 50 點；模擬取樣間隔固定 0.001 s，總時間固定 2 s。完整候選值與誤差以 N/s 儲存；有限掃描範圍與網格不保證可完全相等。匹配高度同時輸出為 `hl_rear_roll_center_m`，供後續 Roll／阻尼分析使用。

前軸參考由 `rc_front_optimal_height_m`、`rc_front_min_peak_rate_N_per_s` 自動取得，單獨執行時會重算前置分析。`hl_front_roll_center_m` 及 `hl_rear_roll_center_m` 分別由前軸最佳化與後軸匹配節點輸出，不再手動設定。
