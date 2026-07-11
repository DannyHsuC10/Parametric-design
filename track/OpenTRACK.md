# OpenTRACK 運作說明

* [輸出結果](/track/OpenTRACK%20Tracks/OpenTRACK.md)
* [檔案位置](opentrack.py)

## 目的

這個工具主要依照 matlab openlap 中的賽道處理工具進行優化製作而成，擁有更進一步的賽道分析方便後續車輛設計使用。

>來源 :  https://github.com/mc12027/OpenLAP-Lap-Time-Simulator

## 主要運作流程

1. 讀取 `input_map.xlsx`。
2. 解析 Excel 中 `Info`、`Shape`、`Elevation`、`Banking`、`Grip Factors`、`Sectors` 等工作表。
3. 將 `Shape` 表中的每個段落展開成連續 mesh 點。
4. 將段落層級的高程、banking、抓地係數、sector 資料擴展到所有賽道點上。
5. 計算原始曲率 $\kappa_{\text{raw}}$，並對其進行 Gaussian 平滑得到 $r$。
6. 進行 apex 峰值偵測，標記左右彎 apex 的位置、曲率強度與距離座標。
7. 將計算結果寫入 `.npz`、`.log`，並輸出圖像檔於 `OpenTRACK Tracks/`。

## 輸入檔案說明

- `input_map.xlsx`
  - `Info`：賽道基本資訊，包含名稱、國家、城市、類型、配置、方向、鏡射等。
  - `Shape`：賽道幾何段落，支援 `LINE` 與 `ARC`。
  - `Elevation`：段落高程值 $Z$。
  - `Banking`：段落 banking 值。
  - `Grip Factors`：段落抓地係數 $\mu$。
  - `Sectors`：段落 sector 編號。

## 主要計算細節

### 賽道幾何重建

`opentrack.py` 以 `mesh-size` 作為最大網格間距 $\Delta s$，將每個段落展開成連續點列。

#### LINE 段落

給定起點 $P_0=(x_0,y_0)$ 與終點 $P_1=(x_1,y_1)$，直線長度為：

$$
L = \sqrt{(x_1 - x_0)^2 + (y_1 - y_0)^2}
$$

切分數為：

$$
N = \max\left(1,\left\lceil\frac{L}{\Delta s}\right\rceil\right)
$$

每個步進距離：

$$
\delta = \frac{L}{N}
$$

方向單位向量：

$$
\mathbf{u} = \left(\frac{x_1-x_0}{L},\ \frac{y_1-y_0}{L}\right)
$$

第 $k$ 個網格點：

$$
P_k = P_{k-1} + \delta\,\mathbf{u},\qquad k=1,2,\ldots,N.
$$

直線片段的原始曲率為：

$$
\kappa_{\text{raw}} = 0.
$$

#### ARC 段落

對於圓弧段，圓心為 $(c_x,c_y)$，半徑為 $R$，起點角度：

$$
\theta_0 = \operatorname{atan2}(y_0 - c_y,\ x_0 - c_x)
$$

弧長與半徑的關係：

$$
L = R\,|\Delta\theta|
$$

方向符號定義：

$$
s = \begin{cases}
-1, & \text{Clockwise（右彎）} \\[2pt]
+1, & \text{其他（左彎）}
\end{cases}
$$

切分數：

$$
N = \max\left(1,\left\lceil\frac{L}{\Delta s}\right\rceil\right)
$$

角度步進：

$$
\delta\theta = \frac{s\,L}{R\,N} = \frac{s\,\Delta\theta}{N}
$$

第 $k$ 個角度：

$$
\theta_k = \theta_{k-1} + \delta\theta
$$

第 $k$ 個點座標：

$$
P_k = \bigl(c_x + R\cos\theta_k,\ c_y + R\sin\theta_k\bigr)
$$

圓弧曲率為：

$$
\kappa_{\text{raw}} = \frac{s}{R}
$$

其中正號代表左彎，負號代表右彎。

### 曲率與半徑

曲率是描述曲線彎曲程度的物理量。對於平面曲線 $\mathbf{r}(s) = (x(s),y(s))$，弧長參數 $s$ 下的曲率定義為：

$$
\kappa = \left\|\frac{d\mathbf{T}}{ds}\right\|,
$$

其中 $\mathbf{T}=\frac{d\mathbf{r}}{ds}$ 為切線單位向量。

程式對離散曲線使用 `LINE` 與 `ARC` 的解析曲率，形成原始曲率向量 $\boldsymbol{\kappa}_{\text{raw}}$。

平滑處理採用 Gaussian kernel：

$$
w_i = \exp\left(-\frac{1}{2}\left(\frac{i}{\sigma}\right)^2\right),\qquad i=-R,\ldots,R,
$$

其中 $R=\left\lfloor\frac{W}{2}\right\rfloor$，$W$ 為窗口寬度，標準差為：

$$
\sigma = \max\left(\frac{W}{6},\epsilon\right)
$$

權重正規化：

$$
w_i \leftarrow \frac{w_i}{\sum_{j=-R}^{R} w_j}
$$

平滑曲率為：

$$
r_k = \sum_{i=-R}^{R} w_i\,\kappa_{\text{raw},\,k+i}
$$

採用邊界延拓（edge padding）保持向量長度不變。

瞬時轉彎半徑：

$$
\rho_k = \frac{1}{|\kappa_k|}
$$

若 $\kappa_k=0$，則表示直線段，半徑趨向無限大。

### apex 偵測

apex 為曲率峰值位置，對應賽道轉彎的最強彎心。

候選峰值滿足：

$$
r_k > r_{k-1},\qquad r_k \ge r_{k+1}
$$

或

$$
r_k < r_{k-1},\qquad r_k \le r_{k+1}.
$$

峰值顯著度定義為：

$$
P(k) = |r_k| - \max\bigl(\min_{i<k} |r_i|,\ \min_{i>k} |r_i|\bigr).
$$

程式取最低顯著度：

$$
P_{\text{min}} = 0.20\,\operatorname{percentile}(|\mathbf{r}|,70\%)
$$

並要求 apex 之間的最小距離：

$$
D_{\min} = \max\left(1,\left\lfloor\frac{8.0}{\Delta s}\right\rceil\right)
$$

這保證 apex 之間不會因高頻噪訊被誤判過多。

輸出 apex 相關欄位：

- `apex_index`
- `apex_s`
- `apex_type`
- `apex_strength`
- `apex_mask`

### 坡度計算

坡度描述高度變化對車輛動力的影響。對離散高程 $Z_k$ 與累積距離 $x_k$，計算斜率：

$$
\tan\alpha_k = \frac{Z_{k+1}-Z_k}{x_{k+1}-x_k}.
$$

程式使用小角近似，將坡度轉為角度：

$$
\operatorname{incl}_k = -\frac{180}{\pi} \frac{Z_{k+1}-Z_k}{x_{k+1}-x_k}.
$$

符號約定中負號表示上坡，正號表示下坡。

以 5 點移動平均平滑：

$$
\operatorname{incl}^{\text{smoothed}}_k = \frac{1}{5} \sum_{i=k-2}^{k+2} \operatorname{incl}_i.
$$

此處使用邊界延拓保持向量長度一致。

## 輸出內容

`OpenTRACK Tracks` 資料夾輸出以下檔案：

- `OpenTRACK.npz`
- `OpenTRACK.log`
- `OpenTRACK_xy_map.png`
- `OpenTRACK_radius.png`
- `OpenTRACK_curvature_fft_frequency.png`
- `OpenTRACK_curvature_fft_wavelength.png`
- `OpenTRACK_radius_time_distribution.png`
- `OpenTRACK_elevation.png`
- `OpenTRACK_inclination.png`
- `OpenTRACK_banking.png`
- `OpenTRACK_grip_factor.png`
- `OpenTRACK_radius_length_distribution.png`

`OpenTRACK.npz` 主要包含：

- $X, Y$：中心線座標。
- $x$：累積距離。
- $\kappa_{\text{raw}}$：原始曲率。
- $r$：平滑曲率。
- $Z$：高程。
- $\operatorname{incl}$：坡度。
- $bank$：banking。
- $factor\_grip$：抓地係數。
- $sector$：sector 編號。
- $apex\_index$：apex 索引。

`OpenTRACK.log` 記錄環境與分析摘要，包括輸入檔案、生成時間、點數、總長度、mesh size、apex 數量、最小半徑與文字地圖。
