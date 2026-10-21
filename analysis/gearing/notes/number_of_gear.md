# Number_of_Gear：行星齒輪數量檢查

以太陽輪齒數 $Z_s$、第一級行星輪齒數 $Z_{p1}$ 與行星輪組數 $N_p$，比較佔用角度與均分間隔。

$$q=\frac{Z_{p1}+2}{Z_{p1}+Z_s},\qquad \theta=2\arcsin\left(\mathrm{clip}(q,-1,1)\right)$$

$$\theta_{limit}=\frac{2\pi}{N_p},\qquad \theta_{next}=\frac{2\pi}{N_p+1}$$

當 $\theta>\theta_{limit}$ 時判為幾何干涉；若 $\theta_{next}<\theta\leq\theta_{limit}$，目前組數接近極限；其餘可再評估增加組數。角度以 rad 計算。
