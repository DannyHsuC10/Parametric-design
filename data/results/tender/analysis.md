# Tender 分析

看看加入 tender 之後的影響，這會讓 pitch 和 heave 的量稍微超出原先設定值。Anti 幾何比例由使用者手動設定，Tender 依該比例計算前後行程、heave 和 pitch。

## 分析目的

分析主彈簧與 tender 彈簧的串聯響應，估算不同煞車加速度與下壓力下的前後懸吊行程、車身 heave、pitch 與 pitch gradient。

## 剛度參數來源

`K_heave_main_N_per_m` 與 `tender_to_heave_stiffness_ratio` 由前序 `2_spring` 自動傳入，無需在本分析輸入。前者是主彈簧剛度（N/m），程式轉為 N/mm 進行行程計算；後者為 tender 剛度與主彈簧剛度的比例：

$$
K_{tender}=K_{heave,main}\times tender\_to\_heave\_stiffness\_ratio
$$

兩彈簧在 tender 尚未壓實時的等效 heave 剛度為：

$$
K_{series}=\frac{K_{heave,main}K_{tender}}
{K_{heave,main}+K_{tender}}
$$

`ms`、`mu`、`L`、`h_cog` 與 `F_ref_ratio` 取自共用參數。`aero_cl_cd_F_ref_N` 由前序 `Aero CL CD` 傳入，等於 skidpad 目標下壓力 `F_ref`。使用者輸入 anti 幾何比例 `anti_geometry_ratio`（0 至 1），以及 `F_ref_ratio`（0 至 1）。

本分析的最大下壓力設定為：

$$
F_{down,max}=aero\_cl\_cd\_F\_ref\_N\times F\_ref\_ratio
$$

圖表使用 0%、25%、50%、75% 與 100% 的 $F_{down,max}$ 作為下壓力情境。例：若 `F_ref_ratio=0.8`，最高情境使用 $0.8F_{ref}$。

## Anti 幾何效果

Anti 比例用於折減煞車造成的縱向載荷轉移：

$$
F_{transfer}=\frac{m a_x g h_{cog}}{L}(1-anti\_geometry\_ratio)
$$

分析以主彈簧與 tender 彈簧的分段力—行程關係求解前後懸吊平衡。「主要結果｜懸吊行程、Heave 與 Pitch」以四個子圖顯示前後行程、heave 與 pitch；pitch gradient 另放在單獨的圖片，從選單切換。圖表標題會顯示手動設定的 anti 比例與最大施加下壓力，結果另輸出測試範圍內的最大壓縮與最大伸長量，供使用者檢查行程是否合適。

每個下壓力與煞車加速度組合會分別求解。行程以原先平衡位置為零點，因此負行程代表懸吊伸長，正行程代表壓縮；兩者都保留。即使求解器回報未收斂，只要迭代結果是有限數值，也會將該點畫出；平衡殘差仍用來區分收斂與未收斂結果，但不作為刪點條件。只有求解器發生例外或回傳非有限數值時才略過。Pitch gradient 以所有已繪製點計算，至少需要兩個點。執行摘要會列出收斂點、未收斂但已繪圖的點，以及略過點數量。
