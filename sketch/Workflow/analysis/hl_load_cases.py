"""加速／煞車／過彎準靜態工況."""

from .hl_damping.parameters import plugin_metadata
from .hl_damping.workflow import run_stage

globals().update(plugin_metadata("hl_load_cases"))


def main(parameters):
    return run_stage("hl_load_cases", parameters)
