# roll_center：正規化等效剛性

以 RC 高度與重心高度之比 $r=h_{rc}/h_{cg}$，比較原始程式的兩路正規化剛性模型。$c=K_c/K_s$ 為車架／懸吊等效線性剛性比，預設為 10。

$$\alpha=1-r$$

$$\frac{K_{eq}}{K_s}=(1-r)^2+cr^2$$

解析最小值為：

$$r_{min}=\frac{1}{1+c},\qquad \frac{K_{eq,min}}{K_s}=\frac{c}{1+c}$$

保留原程式在 0～1 間的 300 點曲線，另列解析解與網格最小點。此正規化指標用於原模型的比較；後續前後軸分析另外以載重轉移率峰值作目標。

流程：車架剛度與整車等效剛性 → roll_center → roll_center_min_load_f → roll_center_same_load_r。
