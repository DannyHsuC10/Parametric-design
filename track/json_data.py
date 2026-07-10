# json_data.py
import numpy as np
import json
from pathlib import Path

# 取得目前這個 .py 檔案所在資料夾
current_dir = Path(__file__).resolve().parent

class file_data:
    def __init__(self,path):# 設定
        self.load_json(path)

    def save_json(self, filename="track_data.json"):# 存檔
        """Save all attributes to a JSON file."""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.__dict__, f, indent=4)
        print(f"Saved track data to {filename}")

    def load_json(self, filename="track_data.json"):# 載入
        """Load attributes from a JSON file."""
        with open(filename, "r", encoding="utf-8") as f:
            self.__dict__.update(json.load(f))

    def print_data(self):# 印出資料
        """Print all track data."""
        print("=" * 50)
        print("track Data")
        print("=" * 50)
        for key, value in self.__dict__.items():
            print(f"{key:25s}: {value}")
        print("=" * 50)



if __name__ == "__main__":
    data = file_data(current_dir / "track.json")# 可以直接設定檔案路徑

    # 也可以之後載入
    #data.load_json(current_dir / "track.json")
    data.load_json(current_dir / "tire.json")

    print(data)
    data.print_data()

