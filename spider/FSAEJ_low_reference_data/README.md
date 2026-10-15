# FSAE Japan 低參考價值資料

本資料夾保存從日本學生 Formula 賽事官方節目 PDF 擷取的車輛資料。PDF 版面與掃描品質不一，解析結果可能不完整或有 OCR 誤讀；使用前請回查原始 PDF。這些資料目前不屬於專案主要視覺化工具的預設資料來源。

## Python 程式

### `parse_fsaej_text_pdfs.py`

解析可選取文字或表格的舊版 PDF：

- 預設搜尋 `PDF_file/` 中檔名符合 `program*.pdf` 的檔案。
- 使用 `pdfplumber` 擷取表格，整理車隊、年份、車輛尺寸、輪胎、引擎與其他車輛欄位。
- 預設輸出 `FSAEJ_text_vehicle_database.csv`。
- CSV 欄位包含車輛資料及 `source_pdf`、`source_page`，方便回查來源。

在本資料夾執行：

```powershell
python parse_fsaej_text_pdfs.py
```

可指定 PDF 資料夾和輸出檔案：

```powershell
python parse_fsaej_text_pdfs.py --pdf-dir PDF_file --output FSAEJ_text_vehicle_database.csv
```

### `parse_fsaej_image_pdfs.py`

解析掃描影像型或新版格式的 PDF：

- 預設搜尋 `PDF_file/` 中檔名以 `学生フォーミュラ` 或 `FSAEJ` 開頭的 PDF。
- 先嘗試使用 PDF 內嵌文字；若無法取得車輛資料，再將頁面轉成圖片並使用 Tesseract OCR。
- OCR 預設語言為 `jpn+eng`，解析完成後輸出 `FSAEJ_image_vehicle_database.csv`。
- 預設使用 220 DPI，OCR 暫存圖片放在 `tmp/fsaej_image_pages/`，完成後會清除；加上 `--keep-images` 可保留暫存圖片。

在本資料夾執行：

```powershell
python parse_fsaej_image_pdfs.py
```

常用選項：

```powershell
python parse_fsaej_image_pdfs.py --pdf-dir PDF_file --output FSAEJ_image_vehicle_database.csv --lang jpn+eng --dpi 220
```

若 Tesseract 不在系統 PATH，可用 `--tesseract-path` 指定執行檔：

```powershell
python parse_fsaej_image_pdfs.py --tesseract-path "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

純影像 PDF 需要安裝 Tesseract，並備妥日文與英文語言資料。程式目前會呼叫 Poppler 的 `pdftoppm` 將 PDF 轉成圖片；其執行檔路徑設定在 `parse_fsaej_image_pdfs.py` 的 `PDFTOPPM` 常數中，若換到不同電腦或 Poppler 安裝位置不同，需要先更新該路徑。只有內嵌文字可解析的 PDF 不需要進行 OCR。

## 執行環境

兩支程式都需要 Python 與 `pdfplumber`。影像解析程式另外需要 Pillow；只有執行純影像 PDF 的 OCR 流程時才需要 Poppler、Tesseract 和 Tesseract 的 `jpn`、`eng` 語言資料。

若在專案根目錄安裝套件，可執行：

```powershell
python -m pip install pdfplumber pillow
```

## 資料與輸出

- `PDF_file/`：來源 PDF。
- `FSAEJ_text_vehicle_database.csv`：文字／表格 PDF 解析結果。
- `FSAEJ_image_vehicle_database.csv`：影像型 PDF 解析結果。
- `tmp/`：測試或 OCR 頁面圖片等暫存檔。

兩支程式各自重建其輸出 CSV；執行時請確認輸出路徑指向預期檔案。文字解析與 OCR 的欄位架構相同，但兩份 CSV 是分開產生，並未自動合併或去重。
