# max_load 輪胎力上限：計算方程式

## 共用符號與單位

四輪索引固定為 $i\in\{FL,FR,RL,RR\}$。座標採 $x$ 向前、$y$ 向左、$z$ 向上；正縱向加速度使前軸卸載，正側向加速度使右側增載。

- $m_s$：全車簧上質量，對應 `ms`；$m_u$：單輪簧下質量，對應 `mu`，單位皆為 kg。
- $L$：軸距；$h$：全車重心高度；$t_f,t_r$：前、後輪距，單位皆為 m。依序對應 `L`、`h_cog`、`t`、`hl_rear_track_m`。
- $f$：前軸靜態重量比例，對應 `hl_front_weight_ratio`；後軸比例為 $1-f$。
- $D$：總下壓力，向下為正，單位 N，對應 `wl_downforce_N`；$\eta$：空力前軸分配比例，對應 `wl_aero_front_ratio`。
- $N_i$：第 $i$ 輪法向載重，向上為正，單位 N。

總質量與重力加速度為：

$$
m=m_s+4m_u,\qquad g=9.81\ \mathrm{m/s^2}
$$

CSV 的 `ax`、`ay` 是以 g 為單位的無因次輸入，以下以 $\gamma_x,\gamma_y$ 表示；代入方程式前先換算成 SI 加速度：

$$
a_x=g\gamma_x,\qquad a_y=g\gamma_y
$$

以下兩個量供四個節點共用：$W$ 為重力與下壓力的總承載，$\Delta_x$ 為前軸轉移到後軸的載重量。

$$
W=mg+D,\qquad \Delta_x=\frac{ma_xh}{L}
$$

前、後軸總載重分別為：

$$
N_f=mgf+D\eta-\Delta_x
$$

$$
N_r=mg(1-f)+D(1-\eta)+\Delta_x
$$

因此 $N_f+N_r=W$。前軸與後軸的縱向轉移量大小相等，保留正負號以涵蓋加速與煞車。下壓力視為固定工況值，作用點沒有橫向偏移。

## max_load：指定工況的輪胎力上限

讀取 sus_load 在指定工況的輪載，定義原始垂向力及截零後的接觸力參考值：

$$
F_{z,i}^{raw}=N_i^{sus},\qquad F_{z,i}^{+}=\max(F_{z,i}^{raw},0)
$$

令 $\mu_x$ 對應既有 `mu_w`、$\mu_y$ 對應 `wl_mu_y`。各輪縱向、側向獨立力上限為：

$$
F_{x,i}^{lim}=\mu_xF_{z,i}^{+},\qquad F_{y,i}^{lim}=\mu_yF_{z,i}^{+}
$$

因此單一方向分別滿足：

$$
|F_{x,i}|\leq F_{x,i}^{lim},\qquad |F_{y,i}|\leq F_{y,i}^{lim}
$$

### 摩擦橢圓示意

當兩個方向上限皆大於零時，示意性的組合力限制為：

$$
\left(\frac{F_{x,i}}{\mu_xF_{z,i}^{+}}\right)^2+\left(\frac{F_{y,i}}{\mu_yF_{z,i}^{+}}\right)^2\leq1
$$

橢圓邊界圖使用參數 $\psi\in[0,2\pi]$：

$$
F_{x,i}=\mu_xF_{z,i}^{+}\cos\psi,\qquad F_{y,i}=\mu_yF_{z,i}^{+}\sin\psi
$$

兩方向的獨立上限不能同時取滿。若某方向摩擦係數為零，該方向力上限即為零；若輪載截零，則兩方向力上限皆為零。橢圓僅為組合力示意，沒有輪胎負載敏感度或操穩極限求解。

### 輸出摘要與有效性

程式的三個最大值輸出是在目前工況比較四輪：

$$
F_z^{max}=\max_i F_{z,i}^{+},\qquad F_x^{max}=\max_i F_{x,i}^{lim},\qquad F_y^{max}=\max_i F_{y,i}^{lim}
$$

這些值沒有對整個加速度包絡再取全域最大。整車接地有效性以所有原始輪載皆非負為條件：

$$
\min_i F_{z,i}^{raw}\geq0
$$

滿足時 `contact_valid` 為 1，否則為 0。若存在負輪載，截零會增加四輪接觸力的總和：

$$
\sum_i F_{z,i}^{+}=mg+D-\sum_{i:F_{z,i}^{raw}<0}F_{z,i}^{raw}
$$

因此截零後的力只能作為參考值，沒有重新求解離地後的接觸力分配。`tire_force_limits.csv` 同時保留原始輪載、截零輪載、方向力上限與接地旗標。

## 流程與執行方式

```mermaid
graph LR
    W1[FWL] --> W2[solver_compar]
    W2 --> W3[sus_load]
    W3 --> W4[max_load]
```

四個節點共用 `data/analysis_flow.csv`，使用 `flow_row=tertiary`，`branch_from` 與 `merge_from` 留空，與原流程之間沒有箭頭。單擊節點編輯參數，雙擊查看圖表、CSV 與本節方程式。

主視窗只有一張流程圖，輪載群組與原流程分離顯示。使用既有的「Run 全流程」或「單獨執行所選分析」，缺少剛性輸出時會補算必要的前置分析。`Ks_pitch_N_per_m`、`Ks_roll_N_per_m` 仍取自共用剛性分析的輸出。

無視窗執行：

```powershell
.venv/Scripts/python.exe -B -X utf8 -m analysis.wheel_load
```

支援 `--csv <參數路徑>` 與 `--output <結果根目錄>`。完整方程式與圖表報告位於 `data/results/wheel_load/index.html`；每個節點的 `analysis.md` 僅保留共用定義與該節計算方程式。
