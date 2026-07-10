import numpy as np
# tire data 
import json
from pathlib import Path

# 取得目前這個 .py 檔案所在資料夾
current_dir = Path(__file__).resolve().parent

class tire_data:
    def __init__(self):
        # Tire
        self.tir_path = "tire.tir"
        self.mu_y = 1.5
        self.mu_x = 1.5
        self.m = 321

    def save_json(self, filename="tire_data.json"):
        """Save all attributes to a JSON file."""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.__dict__, f, indent=4)

    def load_json(self, filename="tire_data.json"):
        """Load attributes from a JSON file."""
        with open(filename, "r", encoding="utf-8") as f:
            self.__dict__.update(json.load(f))



if __name__ == "__main__":# reset
    # --------------------------------------------
    # 建立物件
    tire = tire_data()

    # 存成 json
    tire.save_json(current_dir / "tire.json")

    print("Save complete")


"""
# 使用範例
# --------------------------------------------
from tire_data import tire_data

# 建立新的物件
tire = tire_data()

print("Before")
print(tire.mu_x)
print(tire.mu_y)
print(tire.tir_path)

# 載入
tire.load_json("tire.json")

print("After")
print(tire.mu_x)
print(tire.mu_y)
print(tire.tir_path)
"""
