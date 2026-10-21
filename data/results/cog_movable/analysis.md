# COG_movable：元件質量、重心與慣性

## 座標與幾何
在 `COG_movable` 節點的「重心高度 h_cog（m）」輸入高度，後續節點共用同一值。簧上／簧下質量不顯示輸入框；三份 Excel 檔案路徑固定在 `analysis/COG_movable.py`，不存於 CSV。Excel 使用 `data/input_data` 中既定的三份檔案，質量計算值可在結果表查看。

前、後輪中心 x 座標由使用者在 `COG_movable` 節點手動輸入，基準為 Excel 原點；Excel 的 dx 是各零件重心座標，特別是輪端零件重心，不作為輪心座標。軸距 `L` 由手動輸入的前輪中心 x 減後輪中心 x。簧上元件的 `dy` 直接使用 m；簧下表的 `dy/y` 依原程式與單位列 m/m，乘以該軸輪距。所有元件的一次矩、二次矩與圖表都使用同一組換算後座標。

$$
L=x_f-x_r,\qquad y_{u,f}=(dy/y)t_f,\qquad y_{u,r}=(dy/y)t_r
$$

初始輸入值沿用原參數檔的 1.53 m 軸距，設為前輪中心 x = 0.765 m、後輪中心 x = −0.765 m；請在輸入框改成實際輪心座標。Excel 的輪端元件 dx 不會被當作輪心位置。

## 質量與重心

$$
m=\sum_i m_i,\qquad \mathbf{M}=\sum_i m_i\mathbf{r}_i,\qquad
\mathbf{r}_{CG}=\frac{\mathbf{M}}{m}
$$

$$
ms=m_{sprung},\qquad mu=\frac{m_{u,f}+m_{u,r}}{4},\qquad
mu_{front}=\frac{m_{u,f}}{2},\qquad mu_{rear}=\frac{m_{u,r}}{2}
$$

`ms` 是全車簧上質量；`mu` 是四輪平均，供原有四分之一車與總質量公式使用。Heave／Roll 的前後軸模型改用各軸的 `mu_front`、`mu_rear`。目前這些軸模型仍假設同軸左右質量相同。

$$
f_f=\frac{x_{CG}-x_r}{L}
$$

`hl_front_weight_ratio` 是**全車前軸靜態重量比例**，用於 FWL 與輪胎靜態承載。為保持前後簧下質量不同時的軸載重一致，簧上前軸承載比例另外計算：

$$
f_{s,f}=\frac{m f_f-m_{u,f}}{ms}
$$

此值輸出為 `hl_sprung_front_weight_ratio`，供前後軸 heave 的簧上質量與靜態彈簧承載使用。

## 慣性張量

$$
\mathbf{I}_{CG}=\sum_i m_i\left[(\mathbf{q}_i\cdot\mathbf{q}_i)\mathbf{1}
-\mathbf{q}_i\mathbf{q}_i^T\right],\qquad
\mathbf{q}_i=\mathbf{r}_i-\mathbf{r}_{CG}
$$

$$
I_{xx,s}=\sum_{i\in sprung}m_i\left[(y_i-y_{CG,s})^2+(z_i-z_{CG,s})^2\right]
$$

`hl_sprung_roll_inertia_kg_m2` 使用**僅簧上元件、繞簧上重心的 x 軸**的慣量。`mass_properties.csv` 同時提供簧上、前簧下、後簧下、全車的重心、一次矩、原點與各自重心處的慣性張量。
