"""Normalized stiffness versus roll-center height."""
from analysis.roll_center_analysis.workflow import metadata, run

globals().update(metadata("roll_center"))


def main(parameters):
    return run("roll_center", parameters)
