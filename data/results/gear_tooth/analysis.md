# Gear_tooth：行星齒輪齒數搜尋

$Z_s$、$Z_{p1}$、$Z_{p2}$、$Z_r$ 分別為太陽輪、兩級行星輪及齒圈齒數；$m_n$ 為模數，$D_{max}$ 為齒輪箱直徑，兩者均使用 mm。

$$Z_{max}=\left\lfloor\frac{D_{max}}{m_n}\right\rfloor$$

$$Z_{p2}=Z_r-Z_s-Z_{p1},\qquad 2Z_{p1}+Z_s\leq Z_{max}$$

$$i=\frac{Z_{p1}}{Z_s}\frac{Z_r}{Z_{p2}}$$

除各齒輪最小齒數限制外，程式另使用以下篩選條件：

$$d=\gcd(Z_{p1},Z_{p2})>1$$

$$\frac{Z_sZ_{p2}-Z_rZ_{p1}}{3d}\in\mathbb{Z}$$

保留 $i>i_{avg}$ 的組合，選出最接近目標的齒比，並輸出完整候選表。此處的組裝篩選係數固定為 3；後續節點仍使用手動設定的四組齒數。
