# Roll：Modal／Physical／1DOF 響應比較

## 三種模型

理想 modal damping 可直接指定三個模態的阻尼；physical 模型只有前後兩支 roll damper；1DOF 模型將輪胎柔度折合進總 roll 剛度，只保留簧上 roll 慣量。本節同時比較三種模型在低／高速阻尼下的 step、Bode、峰值與收斂行為。

$$
M\ddot{q}+C\dot{q}+Kq=[mgh\,a_y/g,0,0]^T
$$

實體阻尼器的等效力臂為 MR_roll 乘輪距。以非負最小平方法找出前後阻尼係數，使實體阻尼矩陣接近理想 modal 矩陣；保留 Frobenius 誤差與 relative_fit_error。兩支被動阻尼器通常無法重現任意三自由度 modal damping。

## 圖表與資料

主要圖並排比較低／高速下三種 step。其他圖包含原包的獨立 modal step、Bode、1DOF 響應，以及新增三模型頻率響應比較；幅值比較使用 deg/g。一般比較圖使用 hl_reference_case_g，三模型定量 step 使用 ay。

完整六組 step CSV 含簧上角度，三自由度模型亦保留前後簧下 roll。roll_damped_poles.csv 列出每個極點、自然頻率及實際阻尼比，包含共軛極點兩列。roll_step_metrics.csv 的角度單位為 deg，尚未在 3 秒視窗內收斂的 settling 欄留空。目標 modal zeta 不等同 physical 系統的實際極點阻尼比。
