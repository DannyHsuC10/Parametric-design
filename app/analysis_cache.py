"""Reuse successful node results only when their own inputs still match."""

import csv
import hashlib
import json
from pathlib import Path

from .analysis_data import canonical_parameter_name, parse_analysis_parameters


def input_file_state(plugin):
    """Track file contents, including fixed Excel/CSV/TIR sources outside the UI."""
    state = {}
    for filename in getattr(plugin, "input_files", ()):
        path = Path(filename).resolve()
        try:
            state[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            state[str(path)] = None
    return state


def _write_state(result_dir, state):
    result_dir.mkdir(parents=True, exist_ok=True)
    temporary = result_dir / "cache.json.tmp"
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(result_dir / "cache.json")


def begin_analysis(results_dir, node_id):
    # Keep a failed/interrupted attempt from exposing a partly overwritten export
    # as a reusable legacy result on the next run or application launch.
    _write_state(Path(results_dir) / node_id, {"complete": False})


def remember_analysis(results_dir, row, parameters, outputs, files):
    result_dir = Path(results_dir) / row["node_id"]
    _write_state(result_dir, {
        "version": 1,
        "complete": True,
        "analysis_id": row["analysis_id"],
        "parameters": parameters,
        "outputs": {name: str(value) for name, value in outputs.items()},
        "input_files": files,
        "result_hash": hashlib.sha256((result_dir / "result.csv").read_bytes()).hexdigest(),
    })


def reusable_outputs(results_dir, row, plugin, parameters, files):
    """Return cached outputs, or None if this node needs to be calculated.

    Each node is checked after its producers finish. If a producer reruns but
    returns the same numbers, consumers with unchanged inputs can still be reused.
    """
    result_dir = Path(results_dir) / row["node_id"]
    result_path = result_dir / "result.csv"
    state_path = result_dir / "cache.json"
    try:
        if not (result_dir / "plot.png").is_file() or any(value is None for value in files.values()):
            return None
        if state_path.exists():
            state = json.loads(state_path.read_text(encoding="utf-8"))
            if (state.get("version") != 1 or state.get("complete") is not True
                    or state.get("analysis_id") != row["analysis_id"]
                    or state.get("parameters") != parameters or state.get("input_files") != files
                    or state.get("result_hash") != hashlib.sha256(result_path.read_bytes()).hexdigest()):
                return None
            outputs = state["outputs"]
        else:
            # Existing exports already record the exact inputs. Adopt them without
            # forcing an expensive first rerun, provided source files are no newer.
            if any(Path(path).stat().st_mtime_ns > result_path.stat().st_mtime_ns for path in files):
                return None
            inputs, outputs = {}, {}
            with result_path.open(encoding="utf-8-sig", newline="") as stream:
                for entry in csv.DictReader(stream):
                    name = canonical_parameter_name(entry["name"])
                    if entry["category"] == "輸入量":
                        inputs[name] = entry["number"]
                    elif entry["category"] == "導出量":
                        outputs[name] = entry["number"]
            if set(inputs) != set(plugin.parameters) or parse_analysis_parameters(inputs, plugin.parameters) != parameters:
                return None
        if not isinstance(outputs, dict) or not set(plugin.outputs).issubset(outputs):
            return None
        if any(not isinstance(value, str) or not value.strip() for value in outputs.values()):
            return None
        if not state_path.exists():
            remember_analysis(results_dir, row, parameters, outputs, files)
        return outputs
    except (OSError, UnicodeError, csv.Error, ValueError, KeyError, TypeError, AttributeError):
        return None
