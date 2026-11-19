"""Expose the friction-circle demonstration as a selectable analysis node."""

from .tire_analysis.workflow import TIRE_FILE, run_friction_circle

PLUGIN_ID = "friction_circle"
TITLE = "friction_circle"
DESCRIPTION = "摩擦圓隨滑移率／垂直載荷變化的曲面，沿用 MF_tester 預設展示參數。"
PARAMETERS = {}
REQUIRES = ("tire_model",)
INPUT_FILES = (TIRE_FILE,)
OUTPUTS = {"friction_circle_figure_count": "friction_circle 輸出圖表數"}
main = run_friction_circle
