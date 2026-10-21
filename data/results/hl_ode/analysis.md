# 非線性 ODE：姿態、峰值、收斂與輪胎 Fz

## 縱向 ODE

使用 「Heave 壓縮／回彈與高低速曲線」、「單輪阻尼設定與 Shock Dyno」的分段非對稱曲線，以 RK45 積分前後解耦 heave 軸模型及等效單輪模型。輸入為最大加速／煞車工況的前後負載轉移階躍；模擬 2 秒、900 點，relative tolerance 為 1e-7，absolute tolerance 為 1e-9。

$$
v_d=MR(\dot{z}_s-\dot{z}_u),\qquad F_{d,wheel}=MR\,F_d(v_d)
$$

$$
m_s\ddot{z}_s=-K_w(z_s-z_u)-F_{d,wheel}+F_{ext}
$$

軸模型使用兩輪並聯的輪胎剛度及軸質量；單輪模型使用單輪質量與一半軸力。位移以靜態平衡位置為零，pitch 由前後簧上位移差求得，未加入整車 pitch inertia 耦合。

## 過彎 ODE

新增完整三自由度過彎 ODE，使用 「Roll physical fit／1DOF Shock Dyno」中 physical fit 的分段 roll damper 曲線。前後相對 roll 角速度乘 MR_roll 與輪距，換成阻尼器軸速度；阻尼力再乘同一力臂，轉回廣義阻尼力矩。

$$
M\ddot{q}+Kq+Q_d(\dot{q})=[mgh\,a_y/g,0,0]^T
$$

同時保留原包的低速線性 physical roll Fz 圖供比較。輪胎法向力以靜態單輪重量加上輪胎垂直剛度乘簧下位移估算；側向左右輪位移由簧下 roll 角與半輪距換算。

## 結果與判讀

圖表選單包含加速／煞車位移及 pitch、解耦與單輪非線性比較、煞車 Fz、三自由度過彎 roll／Fz、原始線性 Fz。四份縱向時序 CSV 與 ode_cornering_physical.csv 提供完整數值。

ode_metrics.csv 包含五組姿態響應的解析穩態值、最大絕對峰值、峰值時間、超越量與 2% settling time。穩態與峰值角度單位為 deg；時間窗內尚未收斂時 settling 留空，不能解讀成 0 秒。

模型使用雙向線性輪胎彈簧，未包含輪胎離地後接觸切換、行程止擋或空力。Fz 若小於零，代表該工況已超出保持接地的假設，須檢查輪胎接地與設定。本節最小 Fz 主要輸出取自非線性過彎四輪的整段時序。
