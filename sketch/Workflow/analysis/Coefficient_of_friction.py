"""Friction curves, peak forces, and regression coefficients for later analyses."""

from .tire_analysis.workflow import TIRE_FILE, run_friction

INPUT_FILES = (TIRE_FILE,)

PLUGIN_ID = "coefficient_of_friction"
TITLE = "coefficient_of_friction 分析"
DESCRIPTION = "以最佳胎壓與 camber 計算 Fx／Fy 峰值、通過原點回歸及摩擦係數。"
PARAMETERS = {"tire_pressure_Pa": "float", "tire_camber_deg": "float"}
HIDDEN_PARAMETERS = set(PARAMETERS)
OUTPUTS = {"mu_x_RL": "縱向回歸摩擦係數", "mu_x_max": "縱向最大摩擦係數",
           "mu_y_RL": "橫向回歸摩擦係數", "mu_y_max": "橫向最大摩擦係數",
           "mu_w": "供縱向／傳動／煞車分析使用的 mu_x_RL",
           "wl_mu_y": "供橫向／賽道／Skidpad／輪載分析使用的 mu_y_RL"}
main = run_friction
