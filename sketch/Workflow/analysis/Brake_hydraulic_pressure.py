"""Oil-line expansion curves from the shared input CSV."""
from analysis.braking.workflow import metadata, run

globals().update(metadata("brake_hydraulic_pressure"))


def main(parameters):
    return run("brake_hydraulic_pressure", parameters)
