"""Independent suspension analysis using the suspension_models package."""

from .suspension_models.parameters import plugin_metadata
from .suspension_models.workflow import run_stage

globals().update(plugin_metadata("one_eighth_suspension_model"))


def main(parameters):
    return run_stage(PLUGIN_ID, parameters)

