"""Roll and pitch downforce curves using the upstream estimated lift coefficient."""

from analysis.aerodynamics.parameters import metadata
from analysis.aerodynamics.workflow import run_curves

globals().update(metadata("aero_roll_pitch_analysis"))


def main(parameters):
    return run_curves(parameters)
