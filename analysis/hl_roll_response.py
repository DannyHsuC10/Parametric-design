"""Modal／physical／1DOF 響應比較."""

from .hl_damping.parameters import plugin_metadata
from .hl_damping.workflow import run_stage

globals().update(plugin_metadata("hl_roll_response"))


def main(parameters):
    return run_stage("hl_roll_response", parameters)
