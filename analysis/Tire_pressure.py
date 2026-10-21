"""Choose the tire pressure maximizing lateral force RMS."""

from .tire_analysis.workflow import run_optimization

PLUGIN_ID = "tire_pressure"
TITLE = "最佳胎壓"
DESCRIPTION = "8～14 psi，61×61 側滑角／載荷網格，選取最大 Fy RMS。"
PARAMETERS = {}
REQUIRES = ("tire_model",)
OUTPUTS = {"tire_pressure_psi": "最佳胎壓（psi）", "tire_pressure_Pa": "最佳胎壓（Pa）",
           "tire_pressure_rms_Fy_N": "最佳胎壓的 Fy RMS（N）"}
main = run_optimization
