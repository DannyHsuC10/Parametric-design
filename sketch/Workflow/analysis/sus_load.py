"""Suspension-stiffness wheel-load envelope plugin."""
from .wheel_load.parameters import plugin_metadata
from .wheel_load.workflow import run_stage

globals().update(plugin_metadata("sus_load"))


def main(parameters):
    return run_stage("sus_load", parameters)
