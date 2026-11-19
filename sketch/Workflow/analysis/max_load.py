"""Independent longitudinal and lateral tire-force bounds."""
from .wheel_load.parameters import plugin_metadata
from .wheel_load.workflow import run_stage

globals().update(plugin_metadata("max_load"))


def main(parameters):
    return run_stage("max_load", parameters)
