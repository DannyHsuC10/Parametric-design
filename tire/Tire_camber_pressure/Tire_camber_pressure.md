# Tire Camber 與 Tire Pressure 計算說明

這份文件說明 [Tire_camber.py](Tire_camber.py) 與 [Tire_pressure.py](Tire_pressure.py) 的計算思路與流程。兩者都是利用 Pacejka Magic Formula tire model，探討輪胎在不同外傾角（camber）與胎壓（pressure）下，對力輸出與整體性能的影響。

---

## 1. 計算目標

這兩個腳本的核心目標是：

- 觀察輪胎在不同 camber angle 與 tire pressure 下，橫向力與縱向力的變化。
- 透過數值掃描，找出對輪胎性能最有利的 camber angle 與 tire 
---

## 2. 共通基礎設定

兩個腳本都會先完成以下步驟：

1. 讀取 TIR 輪胎模型參數
   - 使用 `tire.load_tir("tire.tir")` 讀入 Pacejka tire model。

2. 設定掃描範圍
   - 法向載重 $F_z$：從 0 到 1400 N。
   - 滑移率 $SL$：從 $-1$ 到 $1$。
   - 滑移角 $SA$：從 $-10^	ext{o}$ 到 $10^	ext{o}$。

3. 固定其他參數
   - 內傾角（inclination angle）固定為 0°。
   - 其他條件保持不變，只改變 camber 或 pressure。

4. 建立計算輸入
   - 對每個點都建立 `CalculationInput` 物件。
   - 其內容包含：載重、滑移角或滑移率、胎壓與 TIR 參數。

5. 呼叫 Magic Formula 求解器
   - 針對縱向力使用 `MF_Universal_solver("FX", MF)`。
   - 針對橫向力使用 `MF_Universal_solver("FY", MF)`。

---

## 3. Camber 分析方法

### 3.1 變數設定

在 [Tire_camber.py](Tire_camber.py) 中，會固定以下內容：

- $SL = 0$（用於 Fy 分析）
- $SA = 0$（用於 Fx 分析）
- 依序測試多個 camber angle：
  - $-4, -2, 0, 2, 4$

### 3.2 計算流程

對每一個 camber angle，腳本會：

1. 建立一個力曲面網格。
2. 對每個法向載重 $F_z$ 與對應的滑移變數進行掃描。
3. 計算出一個力分布面 $F_x(F_z, SL)$ 或 $F_y(F_z, SA)$。
4. 將不同 camber angle 的力面畫在同一張圖中，方便比較。

### 3.3 性能評估指標

腳本使用 RMS（Root Mean Square）作為性能指標：

$$
RMS = \frac{1}{N}\sqrt{\sum_{i=1}^{N} F_i^2}
$$

其中 $F_i$ 是不同網格點上的力值。

這個指標可以用來衡量某個 camber angle 在整個掃描範圍內，整體提供力的能力。數值越大，代表該 camber 情況下輪胎在這組條件下的整體力輸出越強。

### 3.4 最佳 camber 的選擇

最後，腳本會比較各個 camber angle 的 RMS 值，選出最大者：

- 取出 RMS 最大的 camber angle。

---

## 4. Tire Pressure 分析方法

### 4.1 變數設定

在 [Tire_pressure.py](Tire_pressure.py) 中，會固定以下內容：

- $SL = 0$（用於 Fy 分析）
- $SA = 0$（用於 Fx 分析）
- 測試多個胎壓：
  - 8 psi、9 psi、10 psi、11 psi、12 psi、13 psi、14 psi

接著將 psi 轉換為 Pa：

$$
P = \text{psi} \times 6894.757293168
$$

### 4.2 計算流程

對每一個胎壓，腳本會：

1. 重新建立力曲面網格。
2. 針對不同的 $F_z$ 與滑移角 $SA$ 計算橫向力 $F_y$。
3. 繪製不同胎壓下的 Fy 曲面圖。
4. 計算各個胎壓對應的 RMS 值。

### 4.3 最佳胎壓選擇

最後，腳本會選出 RMS 最大的胎壓，代表在這一組掃描條件下，該胎壓可提供最佳的整體側向力表現。

---

## 5. 這兩個分析的差異

| 項目 | Camber 分析 | Pressure 分析 |
| --- | --- | --- |
| 變化參數 | Camber angle | Tire pressure |
| 主要目的 | 觀察外傾角對力性能的影響 | 觀察胎壓對力性能的影響 |
| 評估指標 | RMS | RMS |
| 輸出結果 | 最佳 camber | 最佳胎壓 |

---

## 6. 物理意義

這兩個分析其實是在探討輪胎在不同幾何與工況下，如何影響其抓地力與力輸出能力：

- Camber 會改變輪胎接地面積與接觸形態，進而影響力的分布。
- Tire pressure 會改變輪胎的剛度與接地特性，也會直接影響力的大小與響應。

因此，這兩個腳本可以視為一種「尋找最佳輪胎設定」的數值分析方法，常用於底盤設計、輪胎性能評估與車輛動態模擬前的參數選擇。
