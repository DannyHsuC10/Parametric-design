# FSG Data Statistics

這個資料夾集中放置目前主要使用的 FSG/FSE 資料與統計輸出。

## raw_data

原始或直接爬取資料：

- `FSG_EV_vehicle_database.csv`：FSG EV 車輛參數資料
- `fse_historical_results.csv`：FSE 歷史成績與賽事排名資料
- `AMZ_vehicle_history.csv`：AMZ 單隊車輛歷史資料

## computed_statistics

由原始資料整理或統計後的輸出：

- `fsg_results_vehicle_year_intersection.csv`：用車隊名稱與年份合併後，有排名也有車輛參數的交集資料
- `fsg_weighted_vehicle_parameter_ranges.csv`：同車隊同年先合併成一筆年度樣本，再依年度最佳名次權重計算的車輛參數常態分布統計與 3σ 範圍

## scripts

處理這些資料的 Python 腳本：

- `scrape_fse_results.py`：爬取 FSE 歷史成績，輸出到 `raw_data/fse_historical_results.csv`
- `spider_all_FSGteam.py`：爬取 FSG EV 車輛參數，輸出到 `raw_data/FSG_EV_vehicle_database.csv`
- `spider_AMZ.py`：爬取 AMZ 單隊車輛資料，輸出到 `raw_data/AMZ_vehicle_history.csv`
- `extract_fsg_result_vehicle_intersections.py`：用車隊名稱與年份合併排名和車輛參數，輸出到 `computed_statistics/fsg_results_vehicle_year_intersection.csv`
- `weighted_vehicle_parameter_ranges.py`：同車隊同年先合併成一筆年度樣本，再依年度最佳名次權重統計車輛參數 3σ 範圍，輸出到 `computed_statistics/fsg_weighted_vehicle_parameter_ranges.csv`

這些腳本的預設路徑都以 `scripts/` 位置推導，因此可以從專案根目錄或 `scripts/` 內執行。

目前網站工具會直接讀取這個資料夾內的 CSV。
