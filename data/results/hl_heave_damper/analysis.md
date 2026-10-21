# 阻尼器：Heave 壓縮／回彈與高低速曲線

## 分析目的

將 Heave 軸端參考臨界阻尼與目標阻尼比換算成實際阻尼器軸端 force-velocity。前後軸各有低速壓縮、低速回彈、高速壓縮、高速回彈四種斜率，可獨立設定。這是理論 Shock Dyno 目標曲線，未包含實測遲滯或氣壓力。

$$
c_{shaft}=\frac{\zeta c_{crit,axle}}{MR_{heave}^2}
$$

轉成 N/(mm/s) 時再除以 1000。採正速度為壓縮、負速度為回彈；knee 以阻尼器軸速度 mm/s 表示。

$$
|F(v)|=c_{low}\min(|v|,v_k)+c_{high}\max(|v|-v_k,0)
$$

曲線在 knee 連續，不是跨過 knee 後將全部速度直接乘高速斜率。正負側分別使用壓縮／回彈斜率。

## 結果

圖表與 shock_dyno.csv 比較前後軸 -250 至 250 mm/s 曲線；damper_coefficients.csv 列出四種斜率及 knee。主要輸出記錄 +250 mm/s 壓縮側的前後軸阻尼力。本節結果亦供 「單輪阻尼設定與 Shock Dyno」 單輪等效與 「非線性 ODE、姿態與輪胎 Fz」 非線性 ODE 使用。
