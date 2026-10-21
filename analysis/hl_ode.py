"""非線性 ODE、姿態與輪胎 Fz."""

from .hl_damping.parameters import plugin_metadata
from .hl_damping.workflow import run_stage

globals().update(plugin_metadata("hl_ode"))


def main(parameters):
    return run_stage("hl_ode", parameters)
