"""Heave 壓縮／回彈與高低速曲線."""

from .hl_damping.parameters import plugin_metadata
from .hl_damping.workflow import run_stage

globals().update(plugin_metadata("hl_heave_damper"))


def main(parameters):
    return run_stage("hl_heave_damper", parameters)
