import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag
from pathlib import Path

# 設定常數
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_ROOT = SCRIPT_DIR.parent
RAW_DATA_DIR = DATA_ROOT / "raw_data"
BASE_URL = "https://www.formulastudent.de/teams/fse/details/tid/{team_id}"
DEFAULT_TEAM_ID = 248


def fetch_soup(team_id: int) -> BeautifulSoup:
    """下載指定 Team ID 的網頁並回傳 BeautifulSoup 物件"""
    url = BASE_URL.format(team_id=team_id)
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def extract_table_data(container: Tag) -> dict[str, str]:
    """從指定的 HTML 容器中提取所有表格的 Key-Value 資料"""
    data = {}
    tables = container.find_all("table")

    for table in tables:
        for row in table.find_all("tr"):
            cols = row.find_all(["td", "th"])
            if len(cols) >= 2:
                key = cols[0].get_text(" ", strip=True)
                val = cols[1].get_text(" ", strip=True)
                data[key] = val

    return data


def parse_car_specifications(soup: BeautifulSoup) -> list[dict[str, str]]:
    """解析頁面中所有 Car Specifications 的車輛數據"""
    spec_headers = soup.find_all(
        string=lambda text: text and "Car Specifications" in text
    )
    print(f"找到 {len(spec_headers)} 個 Car Specifications 區塊")

    cars_data = []
    for i, header in enumerate(spec_headers, start=1):
        print(f"正在處理第 {i} 輛車...")

        # 向上尋找容器區塊
        container = header.find_parent("div", class_=True)
        if not container:
            print(f" ⚠️ 第 {i} 輛車找不到對應的容器，跳過")
            continue

        # 建立車輛資料字典
        car_info = {
            "raw_text": container.get_text("\n", strip=True)[:200]
        }  # Debug 用文字檔頭

        # 提取表格資料並合併
        specs = extract_table_data(container)
        car_info.update(specs)

        cars_data.append(car_info)

    return cars_data


def main():
    team_id = DEFAULT_TEAM_ID
    print(f"開始抓取 Team ID: {team_id} 的資料...")

    try:
        soup = fetch_soup(team_id)
        cars_data = parse_car_specifications(soup)

        if not cars_data:
            print("沒有抓取到任何車輛資料。")
            return

        # 轉為 DataFrame 並輸出 CSV
        df = pd.DataFrame(cars_data)
        output_filename = RAW_DATA_DIR / "AMZ_vehicle_history.csv"
        output_filename.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_filename, index=False, encoding="utf-8-sig")

        print(f"\n處理完成！成功抓取 {len(df)} 筆資料，已儲存至 '{output_filename}'")
        print(df.head())  # 印出前幾筆預覽

    except requests.RequestException as e:
        print(f" 網頁請求失敗: {e}")


if __name__ == "__main__":
    main()
