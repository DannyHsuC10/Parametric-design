# 阻尼器：Roll Physical fit／1DOF sizing

## 定尺寸邏輯

physical fit 以 「Modal／physical／1DOF 響應比較」的非負前後實體阻尼係數建立 roll damper 高低速曲線。1DOF sizing 先依總 roll 剛度與簧上轉動慣量計算所需轉動阻尼，再依前後實際 roll 剛度分配換算成線性阻尼器。

$$
c_\phi=2\zeta\sqrt{K_{roll,total}I_s},\qquad c_{shaft,f}=\frac{c_\phi\lambda_f}{(MR_{roll,f}t_f)^2}
$$

後軸同理。lambda 是包含輪胎柔度的前後實際 roll 剛度分配。Roll damper 沿用原包的對稱壓縮／回彈與共同 knee，與 「Heave 壓縮／回彈與高低速曲線」的 heave 非對稱曲線分開處理。

## 輸出與判讀

主要圖分成前後軸，比較 physical fit 與 1DOF sizing；另保留 physical 曲線。damper_roll_physical.csv 與 damper_roll_1dof.csv 為係數表，roll_shock_dyno.csv 為完整力速資料。roll_physical_damping_fit.csv 列出目標矩陣與可實作矩陣的誤差。

1DOF sizing 對應簡化模型，套入三自由度拓樸後不保證各模態達到指定阻尼比，應回看 「Modal／physical／1DOF 響應比較」的實際響應。低／高速是固定斜率區域的設計值；「非線性 ODE、姿態與輪胎 Fz」 過彎 ODE 使用 physical fit 分段曲線進行連續時域積分。
