"""Ideal front/rear braking distribution."""
from analysis.braking.workflow import metadata, run

globals().update(metadata("brake_ratio"))


def main(parameters):
    return run("brake_ratio", parameters)
