"""Rich analysis results, while retaining the existing figure/output interface."""

from dataclasses import dataclass, field
import csv
import json
from pathlib import Path
from analysis_data import normalize_analysis_parameters


@dataclass
class AnalysisResult:
    figure: object
    outputs: dict = field(default_factory=dict)
    figures: dict = field(default_factory=dict)
    tables: dict = field(default_factory=dict)
    figure_titles: dict = field(default_factory=dict)

    def __iter__(self):
        yield self.figure
        yield self.outputs

    def close(self):
        import matplotlib.pyplot as plt
        for figure in (self.figure, *self.figures.values()):
            plt.close(figure)


def normalize_result(result):
    if isinstance(result, AnalysisResult):
        return result
    if isinstance(result, tuple) and len(result) == 2:
        return AnalysisResult(*result)
    return AnalysisResult(result)


def save_analysis_result(results_dir, node_id, parameters, result):
    parameters = normalize_analysis_parameters(parameters)
    result_dir = Path(results_dir) / node_id
    result_dir.mkdir(parents=True, exist_ok=True)
    result.figure.savefig(result_dir / "plot.png", dpi=300, bbox_inches="tight")
    with (result_dir / "result.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(["category", "name", "number"])
        writer.writerows(("輸入量", name, value) for name, value in parameters.items())
        writer.writerows(("導出量", name, value) for name, value in result.outputs.items())
    for filename, figure in result.figures.items():
        figure.savefig(result_dir / filename, dpi=200, bbox_inches="tight")
    plots = [{"file": "plot.png", "title": result.figure_titles.get("plot.png", "主要結果")}]
    plots.extend({"file": filename, "title": result.figure_titles.get(filename, Path(filename).stem)}
                 for filename in result.figures)
    (result_dir / "plots.json").write_text(json.dumps(plots, ensure_ascii=False, indent=2), encoding="utf-8")
    for filename, frame in result.tables.items():
        filename = filename if filename.endswith(".csv") else f"{filename}.csv"
        frame.to_csv(result_dir / filename, index=False, encoding="utf-8-sig")
    if node_id.startswith("hl_"):
        from analysis.hl_damping.report import write_reports
        write_reports(results_dir)
    if node_id in {"FWL", "solver_compar", "sus_load", "max_load"}:
        from analysis.wheel_load.report import write_reports
        write_reports(results_dir)
    notes_path = result_dir / "analysis.md"
    if notes_path.exists():
        from markdown_renderer import render_markdown_file
        render_markdown_file(notes_path)


def load_plot_choices(result_dir):
    """Use the current export's list, with a fallback for older saved results."""
    result_dir = Path(result_dir)
    try:
        entries = json.loads((result_dir / "plots.json").read_text(encoding="utf-8"))
        choices = [(entry["title"], entry["file"]) for entry in entries
                   if (result_dir / entry["file"]).is_file()]
        if choices:
            return choices
    except (OSError, ValueError, TypeError, KeyError):
        pass
    return [("主要結果", "plot.png")] + [
        (path.stem, path.name) for path in sorted(result_dir.glob("*.png")) if path.name != "plot.png"
    ]
