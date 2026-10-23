# aero 3D

本節點在固定參考車速與 heave 下掃描 Pitch／Roll。速度直接使用上游 `skidpad_test` 的 `v_ref`（km/h），以 $V=v_{ref}/3.6$ 換算為 m/s，不提供速度輸入框。承接 `aero_roll_pitch_analysis` 的 `aero_model_CL0`，使用同一組共用空力係數與參考面積。軸距 `L` 由重心分析導出，輪距使用共用 `t`。

令前軸分配 $b_f=b_0+K_{balance,pitch}p$，左側分配 $b_l=0.5+K_{balance,roll}r$。$p,r$ 以 rad 計算：

$$
F_{FL}=Db_fb_l,\quad F_{FR}=Db_f(1-b_l),\quad
F_{RL}=D(1-b_f)b_l,\quad F_{RR}=D(1-b_f)(1-b_l).
$$

四輪空力合計等於總下壓力 $D$。CoP 以軸距、輪距中點為原點，x 向前、y 向左：

$$
x_{CoP}=L(b_f-0.5),\qquad y_{CoP}=t(b_l-0.5).
$$

當總下壓力為零時，CoP 沒有物理定義，表格沿用原程式的零值約定。

預設 Pitch、Roll 各從 −3° 至 3°，每軸 30 點，共 900 點。圖片選單包含總下壓力與 CL 曲面、CoP 曲面／等高線／截面、前後軸與四輪下壓力、左右不對稱、阻力、CL／CoP 關係及不同 Roll 下的 Pitch 敏感度。原有 22 個資料面板拆成 13 張圖，每張圖含色階軸最多四個 axes。

`aero_surface.csv` 儲存完整網格；`pitch_section.csv` 固定 Roll＝0°，`roll_section.csv` 固定 Pitch＝0°，兩者另行精確計算。`summary.csv` 提供各力與 CoP 的最小、最大及平均值。CoP 角度敏感度由精確截面線性擬合，單位 m/rad。`roll_downforce_moment_N_m` 定義為左右下壓力差乘半輪距，正值表示左側下壓力較大。

極值是有限網格上的結果。此為原程式的姿態多項式與空力分配假設，尚未以 CFD／實測辨識，未回饋至懸吊動態。
