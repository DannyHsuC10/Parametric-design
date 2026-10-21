"""Export every chart from Pacejka MF_tester as the first workflow stage."""

from .tire_analysis.workflow import run_model

PLUGIN_ID = "tire_model"
TITLE = "輪胎模型（MF_tester）"
DESCRIPTION = "Pacejka 模型：15 張力／力矩曲面與 4 張摩擦圓圖。"
PARAMETERS = {}
OUTPUTS = {"tire_model_figure_count": "MF_tester 輸出圖表數"}
main = run_model
