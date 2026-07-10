# OpenTRACK Python 工具說明

這個資料夾是一個用 Python 實作的 OpenTRACK 賽道前處理工具。它會讀取 Excel 格式的賽道定義檔 `input_map.xlsx`，依照直線與圓弧段落重建賽道中心線，將幾何資料網格化成固定間距的點列，計算曲率、坡度、apex 等分析資料，最後輸出可供後續模擬或分析使用的 NumPy `.npz` 檔，以及視覺化用的 `.svg` 和執行紀錄 `.log`。

## 資料夾內容

| 路徑 | 說明 |
| --- | --- |
| `opentrack.py` | 主要程式，負責讀取 Excel、重建賽道、計算分析欄位並輸出結果。 |
| `input_map.xlsx` | 賽道輸入資料，包含基本資訊、幾何形狀、高程、banking、抓地係數與 sector。 |
| `requirements.txt` | Python 相依套件，目前需要 `numpy` 與 `openpyxl`。 |
| `README.md` | 原始簡介文件；目前檔案內容顯示為亂碼，可能是文字編碼不一致造成。 |
| `OpenTRACK Tracks/` | 預設輸出資料夾，內含 `.npz`、`.svg`、`.log`。 |

## 執行方式

安裝相依套件後，可在本資料夾執行：

```powershell
python opentrack.py
```

程式預設會讀取同資料夾下的 `input_map.xlsx`，並輸出到 `OpenTRACK Tracks/`。

也可以指定輸入檔、網格間距與輸出資料夾：

```powershell
python opentrack.py input_map.xlsx --mesh-size 0.5 --output "OpenTRACK Tracks"
```

參數說明：

| 參數 | 預設值 | 說明 |
| --- | --- | --- |
| `input` | `input_map.xlsx` | Excel 賽道定義檔。 |
| `--mesh-size` | `0.5` | 賽道點列的目標最大間距，單位為公尺。值必須大於 0。 |
| `--output` | `OpenTRACK Tracks` | 輸出資料夾。 |

## Excel 輸入格式

目前的 `input_map.xlsx` 有六張工作表：

| 工作表 | 用途 |
| --- | --- |
| `Info` | 賽道基本資訊，例如名稱、國家、城市、類型、配置、方向與鏡射設定。 |
| `Shape` | 賽道幾何段落。每列代表一個 section，類型可以是 `LINE` 或 `ARC`。 |
| `Elevation` | 各 section 的高程資料，輸出為 `Z`。 |
| `Banking` | 各 section 的傾斜角資料，輸出為 `bank`。 |
| `Grip Factors` | 各 section 的抓地係數，輸出為 `factor_grip`。 |
| `Sectors` | 各 section 的 sector 編號，輸出為 `sector`。 |

目前檔案中 `Shape` 有 82 個資料列，其餘 section 對應表也各有 82 個資料列。

### `Info`

程式會讀取 `Info` 工作表前 7 列的第二欄，依序對應：

1. `name`
2. `country`
3. `city`
4. `type`
5. `config`
6. `direction`
7. `mirror`

這些資訊也會用來組合輸出檔名。例如目前資料會輸出成：

```text
OpenTRACK_FSAE_A_24_Closed_Forward.*
```

如果 `mirror` 的值是 `On`，檔名會多加 `_Mirrored`。不過目前程式只改檔名，不會真的鏡射座標。

### `Shape`

`Shape` 是重建賽道的核心資料表。主要欄位如下：

| 欄位 | 說明 |
| --- | --- |
| `section` | Excel 中的段落編號。 |
| `Type` | 幾何類型，支援 `LINE` 與 `ARC`。 |
| `Start_X`, `Start_Y` | 該段起點座標。 |
| `End_X`, `End_Y` | 該段終點座標。 |
| `Center_X`, `Center_Y` | 圓弧中心，只有 `ARC` 會使用。 |
| `Radius` | 圓弧半徑，只有 `ARC` 會使用。 |
| `length` | 該段長度。 |
| `Direction` | 圓弧方向，`Clockwise` 代表右彎，其他非 clockwise 的值會被視為逆時針左彎。 |

如果 `Type` 不是 `LINE` 或 `ARC`，程式會跳過該列並印出警告。

## 程式運作流程

`opentrack.py` 的主要流程如下：

1. `main()` 解析命令列參數。
2. `run()` 讀取 Excel、建立輸出資料夾、設定 log 輸出，並呼叫建構流程。
3. `read_workbook()` 讀取 `Info`、`Shape`、`Elevation`、`Banking`、`Grip Factors`、`Sectors`。
4. `reconstruct_geometry()` 依照 `Shape` 將每個 section 展開成連續座標點：
   - `LINE` 依照起點、終點與 `mesh-size` 線性切分。
   - `ARC` 依照圓心、半徑、方向與弧長切分。
5. `build_track()` 建立完整 track 資料：
   - 對原始曲率 `kappa_raw` 做 Gaussian smoothing，得到 `r`。
   - 依曲率峰值偵測左右彎 apex。
   - 將 section 對應的高程、banking、抓地係數與 sector 擴展到每個網格點。
   - 由高程與距離差分計算坡度 `incl`。
6. `save_svg()` 產生視覺化圖檔。
7. `np.savez_compressed()` 輸出壓縮後的 `.npz` 資料檔。
8. 同步產生 `.log`，記錄輸入資訊、點數、總長度、apex 數量與 ASCII 地圖。

## 輸出檔案

預設輸出位置是 `OpenTRACK Tracks/`。目前資料已產生：

| 檔案 | 說明 |
| --- | --- |
| `OpenTRACK_FSAE_A_24_Closed_Forward.npz` | 主要數值資料，供 Python/NumPy 或後續工具讀取。 |
| `OpenTRACK_FSAE_A_24_Closed_Forward.svg` | 六個 panel 的視覺化圖：XY map、曲率、高程、坡度、banking、抓地係數。 |
| `OpenTRACK_FSAE_A_24_Closed_Forward.log` | 執行紀錄，包含基本資訊、總點數、總長度、mesh size、apex 數量與文字地圖。 |

目前 log 顯示：

| 項目 | 數值 |
| --- | --- |
| Track points | 2458 |
| Track length | 1209.309 m |
| Mesh size | 0.5 m |
| Apex count | 73 |

## `.npz` 資料欄位

`.npz` 是 NumPy 的壓縮資料格式，可用以下方式讀取：

```python
import numpy as np

track = np.load("OpenTRACK Tracks/OpenTRACK_FSAE_A_24_Closed_Forward.npz")
print(track.files)
print(track["X"], track["Y"], track["r"])
```

主要欄位：

| 欄位 | 說明 |
| --- | --- |
| `X`, `Y` | 賽道中心線座標。 |
| `x` | 從起點累積的距離，單位為公尺。 |
| `dx` | 相鄰距離間隔，由 `x` 計算。 |
| `n` | track points 數量。 |
| `kappa_raw` | 未平滑的原始曲率。 |
| `r` | 平滑後曲率。正值代表左彎，負值代表右彎。 |
| `section` | 每個點所屬的原始 Excel section。 |
| `segment_type` | 每個點的段落類型，包含 `LINE`、`LEFT`、`RIGHT`。 |
| `Z` | 高程。 |
| `incl` | 由高程差分估算的坡度角。 |
| `bank` | banking 角度。 |
| `factor_grip` | 抓地係數。 |
| `sector` | sector 編號。 |
| `apex_index` | apex 在點列中的索引。 |
| `apex_s` | apex 對應的累積距離。 |
| `apex_type` | apex 類型，`1` 為左彎、`-1` 為右彎。 |
| `apex_strength` | apex 曲率強度。 |
| `apex_mask` | 與點列等長的布林陣列，標記 apex 位置。 |
| `arrow` | 目前固定輸出為 0。 |
| `info_*` | 從 `Info` 工作表保存的賽道基本資訊。 |

## 重要實作細節

- 幾何重建時，程式不是直接使用 Excel 既有點列，而是根據每段 `LINE` 或 `ARC` 重新生成連續座標。
- `mesh-size` 是目標最大間距；每個 section 會以 `ceil(length / mesh-size)` 決定切分數，因此實際點距可能略小於指定值。
- 曲率平滑使用 7 點 Gaussian kernel。
- apex 偵測根據平滑曲率的峰值 prominence，並用約 8 m 的最小距離限制避免過密峰值。
- `Elevation`、`Banking`、`Grip Factors`、`Sectors` 都是以 section 為單位輸入，輸出時會展開到每個 track point。
- `incl` 是用高程對距離的差分計算，再以 5 點移動平均平滑。
- `save_svg()` 產生的是靜態 SVG，不需要額外軟體即可用瀏覽器開啟。

## 注意事項

- 執行環境需要 Python，並安裝 `requirements.txt` 中列出的套件。
- `Info` 工作表需要有程式預期的列順序；如果缺少第 7 列 `mirror`，輸出檔名組合可能會失敗。
- `Shape` 表的欄名必須與程式碼中使用的欄名一致，例如 `Type`、`Start_X`、`length`、`Direction`。
- `Elevation`、`Banking`、`Grip Factors`、`Sectors` 的資料列數最好與 `Shape` section 數一致；若不足，程式會用最後一筆可用資料補到後面的 section。
- 目前 `Mirror=On` 不會改變座標方向，只會改變輸出檔名。
