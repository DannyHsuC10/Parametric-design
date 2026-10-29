# Roll Center 等效剛性模型與解析推導

假設

- CG 高度
$
h_{cg}
$

Roll Center
$
h_{rc}
$

則

作用在懸吊的力矩比例

$$
\alpha=\frac{h_{cg}-h_{rc}}{h_{cg}}
$$

作用在車體(幾何路徑)比例

$$
1-\alpha
$$

---


因為力量分流，所以等效剛性可寫成

$$
K_{eq}
=
\alpha^2K_s
+
(1-\alpha)^2K_c
$$

注意平方項是因為位移能量

$$
U=\frac12K\theta^2
$$

分力矩後能量會變成比例平方。

## 解析解

微分求極限

$$
K_{eq}(\alpha)
=
\alpha^2K_s+(1-\alpha)^2K_c
$$

$$
\frac{dK_{eq}(\alpha)}{d\alpha} = 2\alpha K_s-2(1-\alpha)K_c=0
$$

得到

$$
\alpha
=
\frac{K_c}{K_s+K_c}
$$

因此最佳 RC 高度

$$
\boxed{
\frac{h_{rc}}{h_{cg}}
=
1-
\frac{K_c}{K_s+K_c}
=
\frac{K_s}{K_s+K_c}
}
$$

### 這個結果其實很有趣

它代表：

- RC 太低 → 幾乎所有力都走懸吊，彈簧變成主要柔度來源。
- RC 太高 → 大部分力直接進入車體，雖然車體很硬(10 倍)，但因為受力比例增加，整體等效剛性又開始上升。
