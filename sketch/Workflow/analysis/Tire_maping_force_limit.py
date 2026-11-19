"""Select tire force mapping after camber optimization."""

from .tire_analysis.mapping_workflow import run_force_limit
from .tire_analysis.tire_mapping_tool import DEFAULT_OUTPUT
from .tire_analysis.workflow import TIRE_FILE

PLUGIN_ID = "tire_maping_force_limit"
TITLE = "tire_maping_force_limit"
DESCRIPTION = "使用最佳胎壓與 camber，顯示固定 Fz=800 N 的輪胎力極限邊界。"
PARAMETERS = {"tire_pressure_Pa": "float", "tire_camber_deg": "float"}
HIDDEN_PARAMETERS = {"tire_pressure_Pa", "tire_camber_deg"}
REQUIRES = ("tire_camber",)
INPUT_FILES = (DEFAULT_OUTPUT, TIRE_FILE)
OUTPUTS = {}
main = run_force_limit
