# Aero 姿態分析

正式流程為「下壓力與升力係數估算 → aero_roll_pitch_analysis → aero 3D」，位於流程圖的「aero 分析」群組。正式入口是 `analysis/aero_roll_pitch_analysis.py` 與 `analysis/aero_analysis_3d.py`；執行時只引用本套件，不依賴 `new/`，也不在匯入時開啟視窗或產生圖片。

## 來源與設定

前置 `aero_cl_cd` 的 `Cl` 是正值下壓力係數，本模型採向上升力為正，使用 `CL0=-Cl`。`A_air` 沿用同一參考面積，空氣密度固定為 1.225 kg/m³。兩個節點直接使用上游 `skidpad_test` 的 `v_ref`（km/h），計算時以 $V=v_{ref}/3.6$ 換算為 m/s；速度不提供輸入框。第一節點將有號基準係數輸出為 `aero_model_CL0`，供 3D 節點使用。軸距 `L` 由重心分析導出；輪距 `t` 使用共用設定。單獨執行「所選分析＋前置分析」時會自動計算必要來源。

| 設定 | 預設 | 單位／意義 |
|---|---:|---|
| `v_ref` | 上游計算值 | 參考速度，km/h，自動帶入並換算為 m/s，不顯示輸入框 |
| `aero_heave_m` | -0.01 | 固定升沉位移，m，向上為正 |
| `aero_angle_min_deg`／`aero_angle_max_deg` | -3／3 | Pitch、Roll 共用角度範圍，° |
| `aero_curve_points` | 121 | 各一維曲線的點數 |
| `aero_surface_points` | 30 | 每個角度軸的點數，預設共 900 個網格點 |
| `aero_CD0` | 1.8 | 基準阻力係數 |
| `aero_Kh`／`aero_Kp`／`aero_Kr` | -5／0.2／0 | CL 一階敏感度，1/m、1/rad、1/rad |
| `aero_Khh`／`aero_Kpp`／`aero_Krr` | 50／30／8 | CL 二階敏感度，1/m²、1/rad²、1/rad² |
| `aero_Kd_h`／`aero_Kd_p`／`aero_Kd_r` | 0／0／0 | CD 敏感度，1/m、1/rad、1/rad |
| `aero_front_balance` | 0.45 | 基準前軸空力比例 |
| `aero_K_balance_pitch`／`aero_K_balance_roll` | 0.2／0.1 | 前軸／左側分配敏感度，1/rad |

角度輸入與圖軸使用度，計算時統一轉成 rad。這沿用原兩支掃描程式實際使用的角度定義；原 `Aero.py` 的部分註解將 pitch／roll 寫成位移，正式介面已明確區分。

## 模型

令升沉為 $h$、Pitch 為 $p$、Roll 為 $r$，則

$$
C_L=C_{L0}+K_h|h|+K_p|p|+K_r|r|+K_{hh}h^2+K_{pp}p^2+K_{rr}r^2,
$$

$$
C_D=C_{D0}+K_{d,h}|h|+K_{d,p}|p|+K_{d,r}|r|,
\qquad D=-\frac{1}{2}\rho A V^2C_L,\qquad F_{drag}=\frac{1}{2}\rho A V^2C_D.
$$

下壓力 $D$ 向下為正，$C_L>0$ 時保留向上的升力結果。前軸比例 $b_f=b_0+K_{balance,pitch}p$，左側比例 $b_l=0.5+K_{balance,roll}r$：

$$
F_{FL}=Db_fb_l,\quad F_{FR}=Db_f(1-b_l),\quad
F_{RL}=D(1-b_f)b_l,\quad F_{RR}=D(1-b_f)(1-b_l).
$$

CoP 以軸距、輪距的中點為原點，x 向前、y 向左：

$$
x_{CoP}=L(b_f-0.5),\qquad y_{CoP}=t(b_l-0.5).
$$

若總下壓力為零，CoP 沒有物理定義；為沿用原程式，表格中以零表示。程式檢查整個角度範圍的空力分配均介於 0～1，阻力係數不得為負。

## 兩個節點的結果

`aero_roll_pitch_analysis` 分別在 Pitch＝0°、Roll＝0° 下掃描另一個角度，輸出兩張下壓力曲線，以及完整 `roll_sweep.csv`、`pitch_sweep.csv`、基準點與模型參數表。

`aero 3D` 輸出下壓力與 CL 曲面、CoP 曲面與等高線、前後軸與四輪下壓力、左右差值、阻力等高線、CL／CoP 關係及 Pitch 敏感度曲線。原程式的 22 個資料面板分為 13 張圖；每張圖含色階軸最多四個 axes，可在小分析頁的圖片選單切換。完整網格存為 `aero_surface.csv`，另存統計摘要與模型參數。

零角度截面另行精確計算，不以偶數網格的中間點冒充 0°。CoP 的四個角度敏感度由精確截面作線性擬合，單位 m/rad。網格極值是有限掃描範圍內的離散結果。

此模型為原程式的多項式姿態敏感度與空力分配假設，尚未以 CFD 或實測辨識；它提供姿態掃描，尚未回饋耦合至懸吊動態模型。
