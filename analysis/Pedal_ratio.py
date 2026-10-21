"""Size pedal leverage for both hydraulic circuits."""
from analysis.braking.workflow import metadata, run

globals().update(metadata("pedal_ratio"))


def main(parameters):
    return run("pedal_ratio", parameters)
