"""Roll 剛度分配與三自由度模態."""

from .hl_damping.parameters import plugin_metadata
from .hl_damping.workflow import run_stage

globals().update(plugin_metadata("hl_roll"))


def main(parameters):
    return run_stage("hl_roll", parameters)
