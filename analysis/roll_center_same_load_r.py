"""Match the rear transfer-rate peak to the optimized front axle."""
from analysis.roll_center_analysis.workflow import metadata, run

globals().update(metadata("roll_center_same_load_r"))


def main(parameters):
    return run("roll_center_same_load_r", parameters)
