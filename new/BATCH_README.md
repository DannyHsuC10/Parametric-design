# 批次懸吊模型實驗

批次腳本會依「模型類型 → 模型 → 工況」分類產生數據與動圖。
所有輸入在 **0.1 s** 啟動，模擬時間 **0–1 s**，預設 dt 為 **0.001 s**。
每份 PKL 包含初始與結束樣本，總共 1001 筆。輸入、加速度與位置都記錄在同一個時間點。
起訖時間與 dt 由 `batch_cases.py` 的 `INPUT_START`、`SIMULATION_TIME`、`DEFAULT_DT` 管理。

## 執行方式

先在 `Model_testing/data_creator.py` 修改檔案上方的 `FAMILY`、`OUTPUT`、`FPS` 與 `DPI`，再由專案根目錄執行：

```powershell
# 使用 data_creator.py 上方設定執行批次實驗
& .\Suspension_sys\.venv\Scripts\python.exe .\Model_testing\data_creator.py

# 只列出配對與排除原因
& .\Suspension_sys\.venv\Scripts\python.exe .\Model_testing\data_creator.py --list

# 選定模型及工況；名稱以 --list 為準
& .\Suspension_sys\.venv\Scripts\python.exe .\Model_testing\data_creator.py --models half half_2dof --scenarios cornering sine_left

# 先產生數據，再從 PKL 補製 GIF
& .\Suspension_sys\.venv\Scripts\python.exe .\Model_testing\data_creator.py --no-gif --output .\Model_testing\batch_results\my_run
& .\Suspension_sys\.venv\Scripts\python.exe .\Model_testing\data_creator.py --gif-only --output .\Model_testing\batch_results\my_run

# 中斷後續跑，只補齊尚未完成的檔案
& .\Suspension_sys\.venv\Scripts\python.exe .\Model_testing\data_creator.py --resume --output .\Model_testing\batch_results\my_run
```

若環境已啟動，也可以直接使用 `python Model_testing/data_creator.py`。LR 工況會自動排除不支援的模型配對。

## 相容配對

| 類型 | 模型 | 可用工況 | 組合數 |
| --- | --- | --- | --- |
| quarter 單輪 | single、one_eighth、double、quarter | step、bump、sine、random | 16 |
| LR 左右雙輪 | 2mass_2dof、2mass | bump_left、bump_both、sine_left | 6 |
| LR 左右雙輪 | half_2dof、half、rollcenter_all | 上述 3 種路面，加 cornering | 12 |
| FR 前後雙輪 | half_2dof、half | impulse_drive、accelerate | 4 |

共 **38** 個相容組合。單輪模型不會收到 LR/FR 輸入；LR 與 FR 也不會互換輸入。
LR 的兩個雙質點模型沒有側向加速度／剛體側傾方程，因此排除它們與 cornering 的 2 個配對。
工況清單由 `batch_cases.py` 的 `FAMILIES` 管理；刪除 `road/` 中的工況函式時，也要同步移除這裡的配對。

## 輸出位置

預設直接輸出到固定的 `Model_testing/batch_results/`，不再建立時間戳記資料夾。
重跑時會覆寫選定模型／工況的結果，其他仍有效工況的檔案與索引會保留；也可用 `--output` 指定其他輸出目錄：

```text
batch_results/
  manifest.json                  # 每項實驗狀態、配對排除原因
  summary.csv                    # 所有實驗的檔案索引與錯誤摘要
  quarter/quarter/bump/
    result.pkl                   # SimulationLogger 相容封裝
    response.gif
  LR/half/cornering/
    result.pkl
    response.gif
  FR/half/accelerate/
    result.pkl
    response.gif
```

每份 PKL 保留 `data`、`metadata` 結構，可透過 `SimulationLogger.load()` 載入。
`metadata['config']` 記錄模型與工況名稱、函式、路面參數、懸吊參數、dt、起訖時間與來源檔案雜湊。
`--resume`／`--gif-only` 會核對設定，避免混用不同模型或參數產生的舊數據。
只需補齊結果時使用 `--resume`；一般執行會重新模擬，並清除該工況舊的 GIF，避免動畫與新數據不一致。
若實驗失敗，會在該工況目錄寫入 `error.txt`，並繼續下一組；整批結束會回傳失敗狀態。
重跑時，`manifest.json` 與 `summary.csv` 會移除已刪除工況的舊索引；既有輸出檔案不會自動刪除。

## 修改實驗設定

- 在 `batch_cases.py` 的 `FAMILIES` 新增模型／工況與相容限制。
- 實際懸吊參數仍由 `Parameter_set/Suspension.py` 提供，批次執行保留當前設定。
- `SuspensionLR`、`SuspensionFR` 僅將避震器設為名義阻尼比 `zeta=0.7`，使用 `c=2*zeta*sqrt(k*m_eff)`。
  LR 升沉使用 `m_eff=ms`，側傾使用 `m_eff=2*Ix/track**2`。
  FR 前後支點使用 `1/m_eff=1/(2*ms)+l_arm**2/Iy`，納入車身質量、俯仰慣性與各自力臂。
  上述設定以車輪端固定的車身通道為基準；FR 使用 4DOF 模型的完整軸力定義，耦合後或簡化模型的各振動模態不保證皆為 0.7。
  剛性為零的直推支路維持零阻尼；輪胎 `ct` 保留既有的 50，LR 車架以獨立的 `zeta_frame=0` 保留原本 `c_frame=0`。
- LR 的 `bump_left`（左輪）與 `bump_both`（雙輪同步）取代原本的 impulse 測試。
  兩者與 quarter `bump` 使用相同的半正弦路面：高度 0.01 m、持續 0.2 s，並記錄解析路面速度；啟動時間為 `INPUT_START`。
- 其餘路面振幅、頻率、脈衝長度、轉彎加速度等都列在 `batch_cases.py` 的工況設定中。
- FR `impulse_drive` 前輪在 0.1 s 遇到路面；後輪保留軸距／速度的物理延遲。
  預設車速 5 m/s、目前軸距 1.53 m，所以後輪在 0.406 s 開始。
- 加速縱向輸入力使用當前模型的 `2 * m_corner` 質量。
- random 每個實驗重新建立生成器，預設 seed=0，同一設定下不同模型收到相同路面。
  可用 `--seed 42` 選擇另一個隨機實現。
- GIF 的 FPS 與 DPI 由 `data_creator.py` 上方的設定控制；PKL 保留完整數值樣本。
  可用 `--fps 30 --dpi 100` 提高動畫品質。動畫會自動在背景儲存，不會開啟視窗。
- LR 雙質點模型沒有獨立 roll 狀態；它們的 GIF 由左右簧上位置差換算側傾，PKL 原始狀態不變。

`rollcenter_all` 使用現有 `h_rc` 設定；目前 h_rc=0 時，其幾何力與 frame 激勵也會是零。
若要保留不同方程或參數的實驗供比較，可用 `--output` 指定不同的輸出目錄。

## 檢查批次清單

```powershell
& .\Suspension_sys\.venv\Scripts\python.exe .\Model_testing\data_creator.py --list
```

預期列出 38 個相容配對，並排除 2 個不支援的 cornering 配對。此命令只檢查清單，不執行模擬或產生輸出。
