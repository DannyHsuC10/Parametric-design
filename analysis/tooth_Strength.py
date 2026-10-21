"""Gear tooth module estimate under bending strength limits."""
from analysis.gearing.workflow import metadata, run
globals().update(metadata("tooth_strength"))
def main(parameters): return run("tooth_strength", parameters)
