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
        self.show_plt = False # 是否繪圖形
        self.Free_Radius = 203.2# 輪胎半徑 (mm)
        self.rim_width = 7*25.4# 輪圈寬度 (mm)
        self.rim_outer_width = 2*25.4# 外輪圈寬度 (mm)
        self.rim_inner_width = self.rim_width-self.rim_outer_width# 內輪圈寬度 (mm)
        self.tire_mass = 5.435# 輪胎重量 (kg)
        self.tire_moment_inertia = 0.1508# 輪胎慣性 (kg*m^2)
        self.Tire_Pressure = None# 輪胎壓力 (Pa)
        self.Vertical_stiffness = None# 垂直剛度 (N/m)
        self.mu_y_RL = None # 回歸摩擦係數
        self.mu_x_RL = None
        self.mu_x_max = None # 最大摩擦係數
        self.mu_y_max = None
        self.camber = None# 輪胎傾角 (deg)
        self.toe = 0# 輪胎前束 (deg)

    def save_json(self, filename="tire_data.json"):
        """Save all attributes to a JSON file."""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.__dict__, f, indent=4)
        print(f"Saved tire data to {filename}")

    def load_json(self, filename="tire_data.json"):
        """Load attributes from a JSON file."""
        with open(filename, "r", encoding="utf-8") as f:
            self.__dict__.update(json.load(f))

    def print_data(self):
        """Print all tire data."""
        print("=" * 50)
        print("Tire Data")
        print("=" * 50)
        for key, value in self.__dict__.items():
            print(f"{key:25s}: {value}")
        print("=" * 50)

if __name__ == "__main__":# reset
    # --------------------------------------------
    # 建立物件
    tire = tire_data()

    # 存成 json
    tire.save_json(current_dir / "tire.json")

    print("Save complete")


tire = tire_data()

# 載入
tire.load_json(current_dir / "tire.json")

print(tire)
tire.print_data()
