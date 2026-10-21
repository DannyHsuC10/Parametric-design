"""Acceleration and top-speed gear ratio estimates."""
from analysis.gearing.workflow import metadata, run
globals().update(metadata("gear_rate"))
def main(parameters): return run("gear_rate", parameters)
