# 共用振動與阻尼模型

本套件提供單自由度振動、阻尼參數換算與四分之一車求解工具，由 `analysis/` 中的分析節點共用。以下方程式對應目前程式實作，並說明不同節點使用的剛性、位移座標與積分方式。

## 1. 檔案與分析入口

| 檔案 | 提供功能 |
|---|---|
| [oscillation_models.py](oscillation_models.py) | 正值檢查、時間取樣、無阻尼解析解、顯式 Euler、能量與能量誤差 |
| [damping_models.py](damping_models.py) | 質量與剛性換算、參考臨界阻尼、RK45、四分之一車路面階躍響應 |
| [__init__.py](__init__.py) | 共用模型套件入口 |

套件本身不建立流程節點，也沒有獨立的 `__main__.py`。分析入口保留在上一層，既有流程設定為 [analysis_flow.csv](../../data/analysis_flow.csv)，共用參數為 [analysis_parameters.csv](../../data/analysis_parameters.csv)。

## 2. 共用符號與單位

| 符號 | 程式參數或變數 | 定義 | 單位 |
|---|---|---|---|
| $M_s$ | CSV 的 `ms` | 全車簧上質量 | kg |
| $m_s$ | `system_settings()` 回傳的 `mass` | 單輪分配的簧上質量 | kg |
| $m_u$ | CSV 的 `mu` | 單輪簧下質量 | kg |
| $K_s$ | `Ks` | 上游提供的彈簧剛性 | N/m |
| $K_t$ | `Kt` | 輪胎垂向剛性 | N/m |
| $MR$ | `MR` | 採用輪端剛性公式的運動比 | 無因次 |
| $k_w$ | `wheel_rate` | 運動比換算後的輪端剛性 | N/m |
| $k_r$ | SDOF 的 `stiffness` | 懸吊與輪胎串聯後的等效剛性 | N/m |
| $c$ | `damping` | 黏性阻尼係數 | N·s/m |
| $\zeta$ | `damping_rate_best_ratio` | 指定的阻尼比或參考阻尼比 | 無因次 |
| $x_s,x_u$ | `xs`, `xu` | 相對靜態平衡位置的簧上、簧下位移 | m |
| $r(t)$ | `road` | 相對初始路面的輸入高度 | m |
| $h_n$ | `step` | 相鄰輸出時間點的間隔 | s |

全車質量只在參數換算時除以四：

$$
m_s=\frac{M_s}{4}.
$$

`system_settings(parameters)` 接收的 `parameters["ms"]` 是全車簧上質量；`quarter_car_response(ms, ...)` 的第一個位置參數則已經是單輪簧上質量。使用後者時，直接傳入前者回傳的 `mass`，避免重複除以四。

## 3. 無阻尼單自由度振動：oscillation_models.py

### 3.1 運動方程式與解析解

對質量 $m$、剛性 $k$，位移以靜態平衡位置為原點：

$$
m\ddot{x}+kx=0,\qquad x(0)=x_0,\qquad \dot{x}(0)=v_0.
$$

自然角頻率與自然頻率為：

$$
\omega_n=\sqrt{\frac{k}{m}},\qquad f_n=\frac{\omega_n}{2\pi}.
$$

`analytical_response()` 回傳位移與速度：

$$
x(t)=x_0\cos(\omega_n t)+\frac{v_0}{\omega_n}\sin(\omega_n t).
$$

$$
v(t)=-x_0\omega_n\sin(\omega_n t)+v_0\cos(\omega_n t).
$$

`Analytical_Numerical_Simulation` 與 `Time_sensitivity` 目前使用 $m=M_s/4$、$k=K_s$；這兩個節點不使用後述的輪胎串聯等效剛性 $k_r$。

### 3.2 顯式 Euler 積分

`explicit_euler()` 的位移與速度都使用第 $n$ 步的狀態更新：

$$
x_{n+1}=x_n+h_n v_n.
$$

$$
v_{n+1}=v_n-h_n\frac{k}{m}x_n.
$$

其中 $h_n=t_{n+1}-t_n$。即使最後一個取樣間隔較短，也會使用實際間隔計算。

### 3.3 能量與 Euler 能量漂移

`oscillator_energy()` 計算動能與彈性位能總和：

$$
E_n=\frac{1}{2}m v_n^2+\frac{1}{2}k x_n^2.
$$

當初始能量非零，`energy_error_percent()` 定義：

$$
\varepsilon_{E,n}=\frac{E_n-E_0}{E_0}\times100\%.
$$

當 $E_0=0$ 時，函式回傳全零陣列，避免除以零。

解析解的能量保持不變，但上述顯式 Euler 滿足：

$$
E_{n+1}=\left(1+\omega_n^2h_n^2\right)E_n.
$$

對固定時間步長 $h$ 與非零初始能量：

$$
\frac{E_n}{E_0}=\left(1+\omega_n^2h^2\right)^n.
$$

因此 `Time_sensitivity` 中能量隨時間增加是此積分方式的數值特性。縮小步長可降低有限模擬時間內的漂移；對無阻尼振子，顯式 Euler 不具有保持振幅有界的正步長穩定區間。

### 3.4 時間取樣與輸入檢查

`time_grid(T, h)` 先建立 $0,h,2h,\ldots$，再補入精確終點 $T$；若最後一點已在浮點容許誤差內接近 $T$，則直接將該點設為 $T$。輸出不超出模擬區間。

`T`、`h` 必須有限且大於零，並限制 $T/h\leq2{,}000{,}000$。`require_positive(parameters, *names)` 用於檢查指定參數有限且大於零。解析解、Euler 與能量函式本身不會自動替呼叫端檢查全部輸入。

## 4. 阻尼與等效剛性：damping_models.py

### 4.1 單自由度參數換算

`system_settings(parameters, quarter_car=False)` 先依運動比換算輪端剛性，再與輪胎剛性串聯：

$$
k_w=K_s MR^2.
$$

$$
k_r=\frac{k_w K_t}{k_w+K_t}.
$$

程式採用上式的運動比倍率約定。單自由度模型使用：

$$
m=m_s,\qquad k=k_r,\qquad c_{\mathrm{crit}}=2\sqrt{m_s k_r}.
$$

$$
c=\zeta c_{\mathrm{crit}}.
$$

預設阻尼比取自 `damping_rate_best_ratio`；傳入 `damping_ratio=` 時，使用明確指定的值。阻尼比必須有限且大於等於零。

函式依序回傳 `(mass, stiffness, damping, critical, ratio)`，供 `damping_rate`、`damping_ode` 與 `damping_int` 使用。

### 4.2 四分之一車的參考阻尼

`system_settings(parameters, quarter_car=True)` 使用 $K_s$ 作為懸吊剛性，輪胎剛性 $K_t$ 則保留在第二個自由度中：

$$
k=K_s,\qquad c_{\mathrm{ref}}=2\sqrt{m_s K_s},\qquad c=\zeta c_{\mathrm{ref}}.
$$

這個分支不進行 $MR$ 或串聯剛性換算。$c_{\mathrm{ref}}$ 是以簧上質量與懸吊剛性建立的單自由度參考值；四分之一車具有兩個自由度，$\zeta=1$ 不表示兩個模態都同時達到臨界阻尼。

同一個 `damping_rate_best_ratio` 傳入兩種模型時，因參考剛性不同，得到的 $c$ 也可能不同。

### 4.3 有阻尼單自由度方程式

`damping_rate` 與 `damping_ode` 以平衡位置為原點：

$$
m_s\ddot{x}+c\dot{x}+k_r x=0.
$$

供 RK45 使用的一階形式為：

$$
\dot{x}=v,\qquad \dot{v}=-\frac{cv+k_r x}{m_s}.
$$

對此無外力模型，能量變化率為：

$$
\frac{dE}{dt}=-cv^2.
$$

`checked_solution(rhs, times, initial_state, rtol, atol)` 使用 `solve_ivp(method="RK45")`，在 `times` 指定的位置輸出解，並檢查求解是否成功、結果是否有限。回傳形狀為「狀態數 × 時間點數」的陣列。

預設 `rtol=0.001`、`atol=0.000001`，分析節點可傳入自己的設定。RK45 會自動調整內部積分步長；輸出取樣間隔不等於其內部步長。

## 5. 四分之一車方程式與路面輸入

### 5.1 平衡位置相對座標

`quarter_car_response()` 使用狀態順序 $(x_s,v_s,x_u,v_u)$，重力已由靜態平衡扣除。定義懸吊彈簧與阻尼的合力項：

$$
F_s=K_s(x_s-x_u)+c(v_s-v_u).
$$

兩個質量的運動方程式為：

$$
m_s\ddot{x}_s=-F_s.
$$

$$
m_u\ddot{x}_u=F_s-K_t(x_u-r).
$$

對應的一階形式為：

$$
\dot{x}_s=v_s,\qquad \dot{v}_s=-\frac{F_s}{m_s}.
$$

$$
\dot{x}_u=v_u,\qquad \dot{v}_u=\frac{F_s-K_t(x_u-r)}{m_u}.
$$

### 5.2 路面階躍與分段求解

指定 `road_height` 為 $r_0$、`road_step_time` 為 $t_s$ 時，路面輸入為：

$$
r(t)=0\quad(t<t_s),\qquad r(t)=r_0\quad(t\geq t_s).
$$

若階躍位於求解區間內，函式會在 $t_s$ 分段執行 RK45，將前段的末狀態接到後段初始狀態，再透過連續解插值取得指定時間點的輸出。位移與速度在階躍處連續，加速度可因路面彈簧力變化而跳變。

`road_step_time=None` 表示整段使用零路面輸入。呼叫端應提供至少兩個有限、嚴格遞增的時間點，以及四個初始狀態；回傳陣列形狀為 `4 × len(times)`。

### 5.3 四分之一車能量

與 `quarter_suspension` 節點一致，動能與彈性位能為：

$$
E=\frac{1}{2}m_s v_s^2+\frac{1}{2}m_u v_u^2+\frac{1}{2}K_s(x_s-x_u)^2+\frac{1}{2}K_t(x_u-r)^2.
$$

路面固定時：

$$
\frac{dE}{dt}=-c(v_s-v_u)^2.
$$

路面階躍會改變輪胎彈性位能；有路面輸入的響應不能直接套用無外力、無阻尼模型的能量守恆判準。

## 6. 分析節點與模型差異

| 分析入口 | 使用的共用功能 | 剛性與求解方式 |
|---|---|---|
| [Analytical_Numerical_Simulation](../Analytical_Numerical_Simulation.py) | 解析解、Euler、能量、時間取樣與正值檢查 | $K_s$，無阻尼單自由度 |
| [Time_sensitivity](../Time_sensitivity.py) | 解析解、Euler、能量誤差、時間取樣與正值檢查 | $K_s$，比較不同 Euler 步長 |
| [ode_spring](../ode_spring.py) | 時間取樣、能量誤差與正值檢查 | 自行建立無阻尼四分之一車 RK45；目前輪胎剛性固定為 100,000 N/m |
| [Critical_Damping_Analysis](../Critical_Damping_Analysis.py) | 正值檢查 | 掃描剛性，以 $K_s$ 標示自然頻率與參考臨界阻尼 |
| [damping_rate](../damping_rate.py) | 參數換算、RK45 與單自由度能量 | $k_r$，比較候選阻尼比並輸出 `damping_rate_best_ratio` |
| [damping_ode](../damping_ode.py) | 參數換算與 RK45 | $k_r$，平衡位置相對座標 |
| [damping_int](../damping_int.py) | 參數換算與時間取樣 | $k_r$，含重力的顯式 Euler |
| [quarter_suspension](../quarter_suspension.py) | 參數換算與四分之一車 RK45 | $K_s$ 與 $K_t$，平衡位置相對座標 |
| [quarter_suspension_int](../quarter_suspension_int.py) | 參數換算與時間取樣 | $K_s$ 與 $K_t$，含重力的半隱式 Euler |
| [Damped_oscillation_analysis](../Damped_oscillation_analysis.py) | 參數換算與四分之一車 RK45 | 掃描參考阻尼比，比較簧上位移與輪載變化 |

比較上述節點的圖形時，除了輸入參數，也要對齊初始條件、路面輸入、模擬時間與座標原點。

### 6.1 含重力的單自由度座標

`damping_int` 使用向上為正、保留重力的座標 $z$：

$$
m_s\ddot{z}+c\dot{z}+k_r z=-m_s g,\qquad z_{\mathrm{eq}}=-\frac{m_s g}{k_r}.
$$

轉換為 $x=z-z_{\mathrm{eq}}$ 後，才與 `damping_ode` 的平衡位置相對座標一致。比較初始條件時也要使用 $x_0=z_0-z_{\mathrm{eq}}$。

### 6.2 四分之一車靜態位置與半隱式 Euler

`quarter_suspension_int` 以初始路面為零點，先計算含重力的靜態位置：

$$
z_{u,\mathrm{eq}}=-\frac{(m_s+m_u)g}{K_t},\qquad z_{s,\mathrm{eq}}=z_{u,\mathrm{eq}}-\frac{m_s g}{K_s}.
$$

與 RK45 的相對位移比較時，使用：

$$
x_s=z_s-z_{s,\mathrm{eq}},\qquad x_u=z_u-z_{u,\mathrm{eq}}.
$$

這個節點先以舊狀態計算加速度，再更新速度，最後用新速度更新位置。對任一質量，其步進形式為：

$$
v_{n+1}=v_n+h_n a_n,\qquad z_{n+1}=z_n+h_n v_{n+1}.
$$

這與 `explicit_euler()` 使用舊速度更新位移不同。其路面階躍目前以迴圈時間 $t_n>t_s$ 觸發；與 RK45 對照時也應考慮離散取樣造成的觸發時差。

## 7. 匯入與使用範例

從專案根目錄的程式或 Python 環境使用完整套件路徑匯入。以下建立單輪簧上質量 65 kg、單輪簧下質量 15 kg 的四分之一車路面階躍響應：

```python
from analysis.suspension_dynamics.damping_models import (
    quarter_car_response,
    system_settings,
)
from analysis.suspension_dynamics.oscillation_models import time_grid

parameters = {
    "ms": 260.0,
    "mu": 15.0,
    "Ks": 60000.0,
    "Kt": 100000.0,
    "MR": 1.0,
    "damping_rate_best_ratio": 0.7,
}
mass, stiffness, damping, critical, ratio = system_settings(
    parameters, quarter_car=True,
)
times = time_grid(1.0, 0.001)
xs, vs, xu, vu = quarter_car_response(
    mass, parameters["mu"], stiffness, parameters["Kt"], damping,
    times, initial_state=(0.0, 0.0, 0.0, 0.0),
    road_height=0.05, road_step_time=0.1,
    rtol=1e-7, atol=1e-9,
)
```

範例只回傳狀態陣列；圖表、CSV 與 HTML 結果仍由分析入口與專案儲存流程產生。使用介面時，照常在既有流程中執行分析，雙擊讀取最近一次儲存的結果。
