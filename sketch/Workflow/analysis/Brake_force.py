"""Hydraulic brake force and first wheel-lock boundary."""
from analysis.braking.workflow import metadata, run

globals().update(metadata("brake_force"))


def main(parameters):
    return run("brake_force", parameters)
