# CG：重心高度與傾斜幾何上限

接在 `COG_movable` 後，使用手動輸入的重心高度 `h_cog` 與 Excel 導出的總質量。沿用來源 `new/CG.py` 的 45°、60° 曲線與預設安全係數 1.1，並標示目前輪距與重心。

$$
h_{max}(\theta)=\frac{t}{2\tan(\theta)SF}
$$

`t` 採前後輪距較小值，`SF` 對應可調的 `cg_safety_factor`，必須至少為 1。橫軸為輪距 m，縱軸為重心離地高度 m。

$$
margin_{60}=h_{max}(60^\circ)-h_{cog}
$$

輸出 `cg_height_limit_45_m`、`cg_height_limit_60_m` 與 `cg_height_margin_60_m`。正的 margin 表示目前重心低於這條幾何上限。

此圖是假設左右對稱、無懸吊變形的幾何比較；45°、60° 是來源程式設定的分析角度，並非本工具對當年度賽事規則或實測傾斜測試通過與否的判定。
