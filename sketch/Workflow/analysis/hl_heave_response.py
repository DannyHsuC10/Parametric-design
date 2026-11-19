"""Heave step 與頻率響應."""

from .hl_damping.parameters import plugin_metadata
from .hl_damping.workflow import run_stage

globals().update(plugin_metadata("hl_heave_response"))


def main(parameters):
    return run_stage("hl_heave_response", parameters)
