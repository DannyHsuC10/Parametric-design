# coefficient_of_friction 分析

使用最佳胎壓與 camber 重算縱向／橫向力曲面、峰值力、峰值滑移、摩擦係數曲線，以及通過原點的回歸。Fz=0 不參與回歸與摩擦係數除法。

$$\mu_{\mathrm{RL}}=\frac{\sum_i F_{z,i} F_{\mathrm{peak},i}}{\sum_i F_{z,i}^{2}}$$

`mu_x_RL` 導出為縱向 `mu_w`；`mu_y_RL` 導出為橫向 `wl_mu_y`。賽道與 Skidpad 使用橫向係數；FWL 接續輪胎分析，後續輪胎力上限節點使用兩個方向各自的係數。最大值 `mu_x_max`、`mu_y_max` 另行輸出供比較。

完整分析方法及流程見 [輪胎分析說明](../../../analysis/tire_analysis/README.md)。
