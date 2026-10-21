# 原始分析與整合版：同參數比較

本次直接執行 `new/FWL_solver.py`、`new/sus_load.py` 的原始函式本體，略過 Excel 載入與頂層繪圖。使用現有 CSV 的相同質量、幾何、加速度及換算後的軸端剛度；這是控制變因的公式比較，不是重現未知的舊 Excel 參數。

## 主要差異

- 原版 CG／LSM 在正側向輸入時左側增載，原版 sus_load 則是右側增載。整合版統一為右側增載。因此相同數字的側向輸入會左右對調；將原版 CG／LSM 的側向輸入反號後，最大差異為 0 N。
- 原版 sus_load 把縱向轉移再乘前後 heave 剛度比例。相同工況下，原版總垂向力誤差為 -136.784 N，縱向載重一階矩誤差為 941.76 Nm。整合版這兩項誤差為 4.55e-13 N、-4.55e-13 Nm。
- 原版與前次整合版都用 CG 與 LSM 的差向量當作零空間方向。兩解重合時該方向為零，係數上下界不能描述完整合法解空間。此次改用非零、固定尺度的零空間基底。
- max_load 的截零與摩擦係數乘輪載公式一致；相同摩擦係數下，輪胎力差異由 sus_load 的輪載差異傳遞而來，詳見 `tire_force_comparison.csv`。

## 零空間係數修正

令總承載為 $W=mg+D$，先定義只與輪距相關的無因次方向，再以固定的 $W/4$ 換算成力：

$$
\mathbf{u}=(1,-1,-t_f/t_r,t_f/t_r)^{\mathsf{T}}
$$

$$
\mathbf{v}=\frac{W}{4}\frac{\mathbf{u}}{\max_i|u_i|},\qquad A\mathbf{v}=\mathbf{0}
$$

現在使用 $\mathbf{N}(\alpha)=\mathbf{N}_{LSM}+\alpha\mathbf{v}$，逐輪限制非負。基底不再依賴 CG 與 LSM 的數值差異，係數為無因次量，沿側向掃描維持相同尺度。

前次圖中的固定 [-5, 5] 視窗已取消，陰影僅填入上下界交集非空的工況。當上下界相交，至少兩個輪載可同時達到零；越過交點則不存在四輪非負輪載平衡解。

## 參數與圖面差異

- 目前總質量為 320 kg，由簧上質量加四輪簧下質量取得；原程式直接讀取 `param.m`，舊值未知。
- 原 FWL 與 sus_load 使用同一個 `target_a` 當作兩軸範圍；整合版分別使用 `ax`、`ay`。原 solver_compar 的側向掃描固定為 0–2 g，目前使用 CSV 的側向上限。
- 原 CG／LSM 腳本的額外力為零，原 sus_load 讀取 `F_ref`；目前共用可調下壓力。本次 CG／LSM 比較固定零下壓力與相同前後輪距，以隔離側向符號改變；sus_load 比較則匹配原版的空力前軸比例。
- 原版直接輸入前後軸 heave、roll 剛度；整合版從共用彈簧剛度、運動比與後軸比例換算。本次將換算後相同軸端數值傳給兩版。
- 原 FWL 三維圖的水平軸是 m/s²，整合版是 g；圖面斜率需換算後比較。

詳見 `matched_inputs.csv`、`cg_lsm_comparison.csv`、`suspension_comparison.csv`、`tire_force_comparison.csv`、`equilibrium_errors.csv` 與 `alpha_comparison.csv`。原始來源雜湊保存在 `source_hashes.json`。
