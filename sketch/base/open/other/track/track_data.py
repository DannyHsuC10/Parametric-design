# track_data.py
import numpy as np
import json
from pathlib import Path


# 取得目前這個 .py 檔案所在資料夾
current_dir = Path(__file__).resolve().parent

class track_data:
    def __init__(self):
        # 積分全權重
        self.Skidpad_score = 75
        self.Autocross_score = 100
        self.Endurance_score = 250
        self.total_score = self.Skidpad_score+self.Autocross_score+self.Endurance_score
        self.Skidpad_r = 9.125
        # track
        self.track_path = "input_map.xlsx"
        self.show_plt = False # 是否繪圖形
        self.Track_length = None
        self.Average_radius = None
        self.Name = None
        self.Country = None
        self.Track_points = None
        self.Mesh_size = None
        self.Apex_count = None
        self.track_Minimum_radius = None
        self.top_5_score_rate = None
        self.Radius_distribution_length = []
        self.Radius_distribution_time = []
        self.Radius_distribution_score = []
        
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

if __name__ == "__main__":# reset
    # --------------------------------------------
    # 建立物件
    track = track_data()

    # 存成 json
    track.save_json(current_dir / "track.json")

    print("Save complete")


track = track_data()

# 載入
track.load_json(current_dir / "track.json")

print(track)
#track.print_data()
