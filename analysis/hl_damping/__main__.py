"""Run and export the whole HL package without opening the Qt application."""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from analysis_data import load_analysis_parameters, parse_analysis_parameters
from analysis_result import normalize_result, save_analysis_result
from plugin_loader import scan_analysis
from .parameters import DEFAULTS, STAGES


def main():
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=root / "data" / "analysis_parameters.csv")
    parser.add_argument("--output", type=Path, default=root / "data" / "results")
    args = parser.parse_args()
    values = {name: str(value) for name, value in DEFAULTS.items()} | load_analysis_parameters(args.csv)
    plugins = {plugin.plugin_id: plugin for plugin in scan_analysis()}
    for stage in ("compressed_travel", "aero_stiffness", "frequency_stiffness", "tire_stiffness", *STAGES):
        plugin = plugins[stage]
        parameters = parse_analysis_parameters(values, plugin.parameters)
        result = normalize_result(plugin.run(parameters))
        if stage in STAGES:
            save_analysis_result(args.output, stage, parameters, result)
        values.update({name: str(value) for name, value in result.outputs.items()})
        plt.close(result.figure)
    print(f"Reports: {args.output / 'hl_damping' / 'index.html'}")


if __name__ == "__main__":
    main()
