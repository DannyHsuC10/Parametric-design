# aero_roll_pitch_analysis

本節點承接「下壓力與升力係數估算」，以 `CL0=-Cl` 將正值下壓力係數轉為有號升力係數。參考面積使用共用 `A_air`，空氣密度為 1.225 kg/m³。速度直接使用上游 `skidpad_test` 的 `v_ref`（km/h），以 $V=v_{ref}/3.6$ 換算為 m/s，不提供速度輸入框；固定 heave 由本節點設定。

升沉 $h$ 以 m 表示，Pitch $p$、Roll $r$ 以 rad 計算，圖軸顯示度：

$$
C_L=C_{L0}+K_h|h|+K_p|p|+K_r|r|+K_{hh}h^2+K_{pp}p^2+K_{rr}r^2,
\qquad D=-\frac{1}{2}\rho A V^2C_L.
$$

第一張圖固定 Pitch＝0°，掃描 Roll；第二張圖固定 Roll＝0°，掃描 Pitch。負的 CL 產生正下壓力；正的 CL 保留為負下壓力，表示向上升力。

預設 heave −0.01 m、角度 −3°～3°、各 121 點，參考速度隨上游分析結果更新。`roll_sweep.csv` 與 `pitch_sweep.csv` 保留 CL、CD、總下壓力、阻力、四輪分配及 CoP；`baseline.csv` 是兩個角度均為零的基準點。`model_parameters.csv` 記錄實際使用的係數、面積與幾何。

本節點輸出 `aero_model_CL0` 至後續 `aero 3D`。模型係數為原 `new/Aero.py` 的假設值，尚未進行 CFD／實測辨識，也未與懸吊動態耦合。
