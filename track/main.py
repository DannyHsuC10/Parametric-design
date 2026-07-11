import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# 取得目前這個 .py 檔案所在資料夾
current_dir = Path(__file__).resolve().parent

# 導入資料
import track_data
from json_data import file_data
tire_info = file_data(current_dir/"tire.json")# 導入摩擦係數使用

# 地圖建立
# import DXF_to_lapdata # 創建圖資
import opentrack # 賽道分析與數據建立

print("finich !!!")
