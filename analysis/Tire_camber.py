"""Choose camber at the pressure calculated by the preceding stage."""

from .tire_analysis.workflow import run_optimization

PLUGIN_ID = "tire_camber"
TITLE = "最佳 camber"
DESCRIPTION = "使用最佳胎壓，在 −4.5°～4.5° 的七個 camber 候選值選取最大 Fy RMS。"
PARAMETERS = {"tire_pressure_Pa": "float"}
HIDDEN_PARAMETERS = {"tire_pressure_Pa"}
OUTPUTS = {"tire_camber_deg": "最佳 camber（deg）", "tire_camber_rms_Fy_N": "最佳 camber 的 Fy RMS（N）"}


def main(parameters):
    return run_optimization(parameters, camber=True)
