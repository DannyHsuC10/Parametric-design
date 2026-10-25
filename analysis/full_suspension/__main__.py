"""Generate both cases, including GIFs, without opening the desktop UI."""

from pathlib import Path
import csv
from types import SimpleNamespace

import matplotlib
matplotlib.use("Agg")

from app.analysis_result import save_analysis_result, normalize_result
from app.analysis_cache import begin_analysis, input_file_state, remember_analysis
from app.analysis_data import load_analysis_parameters, parse_analysis_parameters
from app.plugin_loader import scan_analysis
from main import MainWindow


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    plugins = {plugin.plugin_id: plugin for plugin in scan_analysis()}
    values = {name: str(value) for plugin in plugins.values()
              for name, value in plugin.parameter_defaults.items()}
    values.update(load_analysis_parameters(root / "data/analysis_parameters.csv"))
    values = {name: value for name, value in values.items()
              if name not in {output for plugin in plugins.values() for output in plugin.outputs}}
    with (root / "data/analysis_flow.csv").open(encoding="utf-8-sig", newline="") as stream:
        flow = list(csv.DictReader(stream))
    context = SimpleNamespace(flow=flow, plugins_by_id=plugins, parameter_values=values)
    required = MainWindow._required_analysis_rows(context, "full_suspension")
    for row in required:
        plugin = plugins[row["analysis_id"]]
        parameters = parse_analysis_parameters(values, plugin.parameters)
        files = input_file_state(plugin)
        begin_analysis(root / "data/results", row["node_id"])
        current = normalize_result(plugin.run(parameters))
        try:
            # Persist producers as well: single-node runs load their result.csv.
            save_analysis_result(root / "data/results", row["node_id"], parameters, current)
            remember_analysis(root / "data/results", row, parameters, current.outputs, files)
            values.update({name: str(value) for name, value in current.outputs.items()})
        finally:
            current.close()
    print(f"Saved: {root / 'data/results/full_suspension'}", flush=True)
