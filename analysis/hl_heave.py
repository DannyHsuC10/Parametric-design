"""Ride rate 與 Heave 自然頻率."""

from .hl_damping.parameters import plugin_metadata
from .hl_damping.workflow import run_stage

globals().update(plugin_metadata("hl_heave"))


def main(parameters):
    return run_stage("hl_heave", parameters)
