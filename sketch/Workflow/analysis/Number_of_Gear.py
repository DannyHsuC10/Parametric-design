"""Planetary gear count interference check."""
from analysis.gearing.workflow import metadata, run
globals().update(metadata("number_of_gear"))
def main(parameters): return run("number_of_gear", parameters)
