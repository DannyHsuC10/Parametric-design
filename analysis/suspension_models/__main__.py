"""Export selected suspension model analyses with their shared parameter sources."""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

from app.analysis_cache import begin_analysis, input_file_state, remember_analysis
from app.analysis_data import load_analysis_parameters, parse_analysis_parameters
from app.analysis_result import normalize_result, save_analysis_result
from app.plugin_loader import scan_analysis
from .parameters import ROOT, STAGES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", choices=STAGES, default=list(STAGES))
    parser.add_argument("--csv", type=Path, default=ROOT / "data/analysis_parameters.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "data/results")
    args = parser.parse_args()
    plugins = {plugin.plugin_id: plugin for plugin in scan_analysis()}
    defaults = {name: str(value) for plugin in plugins.values() for name, value in plugin.parameter_defaults.items()}
    values = defaults | load_analysis_parameters(args.csv)
    prerequisites = ("cog_movable", "compressed_travel", "aero_stiffness", "frequency_stiffness",
                     "tire_stiffness", "damping_rate", "damped_oscillation_analysis")
    if set(args.models).intersection({"half_suspension_model_lr", "half_rollcenter_all_model"}):
        prerequisites += ("overall_rigidity", "roll_center", "roll_center_min_load_f",
                          "roll_center_same_load_r")
    for stage in (*prerequisites, *dict.fromkeys(args.models)):
        print(f"開始：{stage}", flush=True)
        plugin = plugins[stage]
        parameters = parse_analysis_parameters(values, plugin.parameters)
        files = input_file_state(plugin)
        begin_analysis(args.output, stage)
        result = normalize_result(plugin.run(parameters))
        try:
            save_analysis_result(args.output, stage, parameters, result)
            remember_analysis(args.output, {"node_id": stage, "analysis_id": stage}, parameters, result.outputs, files)
            values.update({name: str(value) for name, value in result.outputs.items()})
        finally:
            result.close()
        print(f"完成：{stage}", flush=True)
    print(f"懸吊模型分析結果：{args.output}")


if __name__ == "__main__":
    main()
