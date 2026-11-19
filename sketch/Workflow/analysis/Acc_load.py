"""Longitudinal load-transfer analysis."""
from analysis.gearing.workflow import metadata, run
globals().update(metadata("acc_load"))
def main(parameters): return run("acc_load", parameters)
