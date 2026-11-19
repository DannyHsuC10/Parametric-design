"""Run the integrated track analysis without opening the desktop interface."""

import argparse
from pathlib import Path


def main():
    from analysis.TrackAnalysis import INPUT_MAP, PARAMETER_DEFAULTS, main as analyze
    from app.analysis_result import save_analysis_result

    parser = argparse.ArgumentParser(description="Analyze an OpenTRACK Excel map.")
    parser.add_argument("input", nargs="?", type=Path, default=INPUT_MAP)
    parser.add_argument("--output", type=Path, default=INPUT_MAP.parents[1] / "results")
    args = parser.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    parameters = dict(PARAMETER_DEFAULTS)
    result = analyze(parameters, input_path=args.input)
    try:
        save_analysis_result(args.output, "track_analysis", parameters, result)
        print(f"Results saved: {args.output.resolve() / 'track_analysis'}")
    finally:
        result.close()


if __name__ == "__main__":
    main()
