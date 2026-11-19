"""Find the front roll center minimizing the peak first-pulse transfer rate."""
from analysis.roll_center_analysis.workflow import metadata, run

globals().update(metadata("roll_center_min_load_f"))


def main(parameters):
    return run("roll_center_min_load_f", parameters)
