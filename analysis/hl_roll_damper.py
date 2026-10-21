"""Roll physical fit／1DOF Shock Dyno."""

from .hl_damping.parameters import plugin_metadata
from .hl_damping.workflow import run_stage

globals().update(plugin_metadata("hl_roll_damper"))


def main(parameters):
    return run_stage("hl_roll_damper", parameters)
