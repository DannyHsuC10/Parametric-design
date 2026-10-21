"""Four-wheel load envelope plugin; original source: new/FWL.py."""
from .wheel_load.parameters import plugin_metadata
from .wheel_load.workflow import run_stage

globals().update(plugin_metadata("FWL"))


def main(parameters):
    return run_stage("FWL", parameters)
