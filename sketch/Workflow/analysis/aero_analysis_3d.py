"""Attitude-dependent aerodynamic surfaces and center-of-pressure analysis."""

from analysis.aerodynamics.parameters import metadata
from analysis.aerodynamics.workflow import run_surfaces

globals().update(metadata("aero_3d"))


def main(parameters):
    return run_surfaces(parameters)
