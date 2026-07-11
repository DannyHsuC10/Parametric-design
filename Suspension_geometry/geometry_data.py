# json_data.py
import numpy as np
import json
from pathlib import Path

# 取得目前這個 .py 檔案所在資料夾
current_dir = Path(__file__).resolve().parent

class geometry_data:
    def __init__(self):# 設定
        
        self.max_SW_angle = 120 # 最大方向盤轉角 (車手熟悉的數值)
        self.L = 1530/1000 # 軸距m (為維持最大靈活)
        #self.

        # =============(繞錐幾何)
        self.r_cone = 228*2**0.5/2/1000 # FSG 角錐資料(m)
        self.Driving_error = 200/1000 # 駕駛誤差(m)
        self.track_width = 10 #賽道寬 (m)
        self.gap_cones = 8 # 角錐間距 (m)
        self.offset_list = [0.01,1/6,1/3] # offset比例


        self.r_min = None

    def save_json(self, filename="geometry_data.json"):# 存檔
        """Save all attributes to a JSON file."""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.__dict__, f, indent=4)
        print(f"Saved geometry data to {filename}")

    def load_json(self, filename="geometry_data.json"):# 載入
        """Load attributes from a JSON file."""
        with open(filename, "r", encoding="utf-8") as f:
            self.__dict__.update(json.load(f))

    def print_data(self):# 印出資料
        """Print all geometry data."""
        print("=" * 50)
        print("geometry Data")
        print("=" * 50)
        for key, value in self.__dict__.items():
            print(f"{key:25s}: {value}")
        print("=" * 50)



if __name__ == "__main__":
    data = geometry_data()# 可以直接設定檔案路徑


    # 存成 json
    data.save_json(current_dir / "geometry.json")

    print("Save complete")



data = geometry_data()

# 載入
data.load_json(current_dir / "geometry.json")

print(data)
data.print_data()
