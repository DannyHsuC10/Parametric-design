"""CG/minimum-norm solver comparison and null-space feasibility."""
from .wheel_load.parameters import plugin_metadata
from .wheel_load.workflow import run_stage

globals().update(plugin_metadata("solver_compar"))


def main(parameters):
    return run_stage("solver_compar", parameters)
