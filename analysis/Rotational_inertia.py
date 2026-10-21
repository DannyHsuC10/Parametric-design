"""Equivalent planetary gear rotational inertia."""
from analysis.gearing.workflow import metadata, run
globals().update(metadata("rotational_inertia"))
def main(parameters): return run("rotational_inertia", parameters)
