"""Vehicle, wheel, grade, and aerodynamic resistance estimate."""
from analysis.gearing.workflow import metadata, run
globals().update(metadata("acc_resis"))
def main(parameters): return run("acc_resis", parameters)
