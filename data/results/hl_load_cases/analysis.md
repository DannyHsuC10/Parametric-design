# 工況：加速／煞車／過彎準靜態分析

## 工況與參數

保留靜態、兩組縱向加速、兩組縱向煞車、兩組側向過彎。hl_reference_case_g 是參考工況；最大加速使用共用 acc_g，最大煞車用 ax，最大過彎用 ay，單位皆為 g。數值相同時仍保留原包兩組工況的列。

$$
\Delta W_x=\frac{(a_x/g)mgh_{CG}}{L}
$$

正加速時前軸減載、後軸增載；heave 彈簧行程由靜態簧上軸重加上轉移量除以軸輪端剛度，再乘 heave 運動比。Pitch 由前後 ride rate 所得位移差與軸距求得；正加速對應本模型負 pitch。

$$
\phi=\frac{(a_y/g)mgh_{CG-RA}}{K_{roll,total}}
$$

Roll 彈簧行程再考慮輪胎與懸吊串聯柔度分配、輪距及 roll 運動比。

## 結果

主要圖依工況比較 pitch／roll 角度、heave／roll 彈簧行程及彈簧力。spring_force_scenarios.csv 保留各工況全部輸出，方便檢查行程與載重。

Heave spring stroke 包含靜態簧上承載；roll_suspension_travel 欄是 roll 彈簧／阻尼器實際行程。這是原包的準靜態簡化，沒有阻尼或暫態峰值；「非線性 ODE、姿態與輪胎 Fz」 再以從靜態平衡位置起算的非線性 ODE 檢查動態情況。
