"""Acceleration and speed simulation from the selected planetary ratio."""
from analysis.gearing.workflow import metadata, run
globals().update(metadata("output_check"))
def main(parameters): return run("output_check", parameters)
