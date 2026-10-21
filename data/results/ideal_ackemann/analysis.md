# ideal_ackemann

使用共用軸距 `L` 與前輪距 `t`，計算理想內、外前輪轉角：

$$\delta_i=\arctan\frac{L}{R-t/2},\qquad\delta_o=\arctan\frac{L}{R+t/2}$$

R 為後軸中心迴轉半徑，必須大於半個前輪距；掃描固定為 3–30 m、51 點，直接定義在 `analysis/ideal_ackemann.py`。介面只保留前輪距 `t` 輸入框（單位 m）；軸距 `L` 使用前置分析結果。

下方圖沿用來源程式的內外輪角差比例：

$$q=\frac{\delta_i-\delta_o}{\delta_i}\,100\%$$

q 與慣用 Ackermann 完成率不同，理想 Ackermann 幾何也不表示 q 必須為 100%。

結果附完整幾何 CSV，流程連到 Bicycle_Model。詳細說明見 `analysis/cornering/README.md`。
