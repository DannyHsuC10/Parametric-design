# OpenTRACK Python

這是原 MATLAB OpenTRACK 賽道前處理工具的 Python 版本。它會讀取 `input_map.xlsx`，重建直線與圓弧賽道、網格化、平滑曲率、偵測 apex，並輸出 NumPy `.npz`、SVG 分析圖與 log。

## 執行

```powershell
python opentrack.py
```

可選參數：

```powershell
python opentrack.py input_map.xlsx --mesh-size 0.5 --output "OpenTRACK Tracks"
```

依賴套件列於 `requirements.txt`。輸出資料夾預設為本資料夾下的 `OpenTRACK Tracks`。

## NPZ 資料

使用方式：

```python
import numpy as np

track = np.load("OpenTRACK Tracks/OpenTRACK_FSAE_A_24_Closed_Forward.npz")
print(track.files)
print(track["X"], track["Y"], track["r"])
```

主要欄位與 MATLAB 輸出相同：`x`、`dx`、`n`、`r`、`bank`、`incl`、`factor_grip`、`sector`、`X`、`Y`、`Z`、`arrow`。此外還保留 `kappa_raw`、`section`、`segment_type` 及 `apex_*` 分析欄位；賽道資訊以 `info_name` 等欄位儲存。

## 與 MATLAB 版的差異

- `.npz` 取代 `.mat`。
- `.svg` 取代 MATLAB `.fig`，可直接用瀏覽器開啟。
- 曲率平滑與 apex prominence 以純 NumPy 重現；演算法意圖相同，但邊界處理與 MATLAB 內建函式可能有些微數值差異。
- 與原程式一致，`Mirror=On` 目前只改變輸出檔名，不會鏡射座標。
