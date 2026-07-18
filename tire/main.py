import numpy as np
import matplotlib.pyplot as plt
from Pacejka_tire_model.model import api as tire

import tire_data

# ttc >> 剛性 & tir >> MF plot
#from Tire_Z_Rigidity import main # 建立剛性
#from Pacejka_tire_model import MF_tester # 繪製所有MF圖形

# tir >> pressure & camber
#from Tire_camber_pressure import Tire_pressure # 建立輪胎壓力
from Tire_camber_pressure import Tire_camber # 建立輪胎傾角

# tir+pressure+camber >> mu
from coefficient_of_friction import mu # 摩擦係數評估
#from coefficient_of_friction import Fx_mu # 建立摩擦係數
#from coefficient_of_friction import Fy_mu # 建立摩擦係數

print("finich !!!")
