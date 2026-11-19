"""單輪彈簧、阻尼與 ARB 等效."""

from .hl_damping.parameters import plugin_metadata
from .hl_damping.workflow import run_stage

globals().update(plugin_metadata("hl_independent"))


def main(parameters):
    return run_stage("hl_independent", parameters)
