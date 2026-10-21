# Roll：剛度分配與三自由度模態

## 分析目的

以 sprung roll、front unsprung roll、rear unsprung roll 三個自由度建立質量與剛度矩陣，計算模態頻率、振型及理想 modal damping。前軸 roll 彈簧取自 Ks_roll_N_per_m，後軸乘 hl_rear_roll_spring_ratio；roll 運動比與 heave 分開設定。

$$
K_{s,roll}=K_{spring,roll}(MR_{roll}t)^2,\qquad K_{t,roll}=\frac{K_tt^2}{2}
$$

$$
K_{actual}=\frac{K_{s,roll}K_{t,roll}}{K_{s,roll}+K_{t,roll}},\qquad \frac{\phi}{a_y/g}=\frac{mgh}{K_{actual,f}+K_{actual,r}}
$$

roll gradient 由最後一式轉為 deg/g；h 是重心到重心位置 roll axis 的垂直距離。簧上轉動慣量使用 hl_sprung_roll_inertia_kg_m2，簧下慣量由單輪簧下質量及輪距估算。

## 模態與阻尼

廣義特徵值問題使用質量正規化振型，各模態的低／高速目標阻尼比由前後軸設定依懸吊 roll 剛度加權。

$$
K\Phi=M\Phi\Omega^2,\qquad C=M\Phi\operatorname{diag}(2\zeta_i\omega_i)\Phi^TM
$$

矩陣自由度順序皆為簧上、前簧下、後簧下；mode_shapes 的欄為 mode 1、2、3，列沿用自由度順序。roll_summary、roll_modes 及質量、剛度、振型與兩種阻尼矩陣皆保存在表格選單。理想 modal 阻尼矩陣供下一節比較實體兩支 roll damper 可達成的結果。
