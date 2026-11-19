"""Search planetary tooth combinations against an overall ratio target."""
from analysis.gearing.workflow import metadata, run
globals().update(metadata("gear_tooth"))
def main(parameters): return run("gear_tooth", parameters)
