"""Workflow entry point for the recorded steady-state lap simulation."""

from analysis.steady_lapsim.workflow import INPUT_FILE, OUTPUTS, run

PLUGIN_ID = "steady_lapsim"
TITLE = "Steady_lapsim"
DESCRIPTION = "讀取既有圈速模擬 PKL，分析賽道速度、加減速階段與圈速摘要。"
PARAMETERS = {}
INPUT_FILES = (INPUT_FILE,)


def main(parameters):
    return run()
