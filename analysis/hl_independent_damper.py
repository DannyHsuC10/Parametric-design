"""單輪阻尼設定與 Shock Dyno."""

from .hl_damping.parameters import plugin_metadata
from .hl_damping.workflow import run_stage

globals().update(plugin_metadata("hl_independent_damper"))


def main(parameters):
    return run_stage("hl_independent_damper", parameters)
