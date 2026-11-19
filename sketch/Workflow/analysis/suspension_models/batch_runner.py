"""Shared engine for the single data_creator.py batch entry point."""

import argparse
from contextlib import redirect_stdout
import csv
from datetime import datetime, timezone
from functools import partial
import hashlib
import json
import os
from pathlib import Path
import traceback

import numpy as np

if __package__:
    from .batch_cases import (
        FAMILIES, INPUT_START, SIMULATION_TIME, DEFAULT_DT, compatibility_error,
    )
    from .data_visualization.Simulation_Logger import SimulationLogger
    from .road.quarter_road import RandomRoad
else:
    from batch_cases import (
        FAMILIES, INPUT_START, SIMULATION_TIME, DEFAULT_DT, compatibility_error,
    )
    from data_visualization.Simulation_Logger import SimulationLogger
    from road.quarter_road import RandomRoad

HERE = Path(__file__).resolve().parent
DEFAULT_OUTPUT = HERE.parents[1] / "data" / "results" / "suspension_batch"


def build_plan(families, models=None, scenarios=None):
    for names, available, label in (
        (models, {n for f in families for n in FAMILIES[f].models}, "models"),
        (scenarios, {n for f in families for n in FAMILIES[f].scenarios}, "scenarios"),
    ):
        unknown = set(names or ()) - available
        if unknown:
            raise ValueError(f"Unknown {label}: {sorted(unknown)}; available: {sorted(available)}")
    cases, skipped = [], []
    for family in families:
        spec = FAMILIES[family]
        for model in spec.models:
            for scenario in spec.scenarios:
                if (models and model not in models) or (scenarios and scenario not in scenarios):
                    continue
                reason = compatibility_error(family, model, scenario)
                case = {"family": family, "model": model, "scenario": scenario}
                if reason:
                    skipped.append({**case, "reason": reason})
                else:
                    cases.append(case)
    if not cases:
        raise ValueError("No compatible cases selected; use --list to inspect the catalog")
    return cases, skipped


def source_hashes(family):
    model_file = {"quarter": "quarter_model.py", "LR": "LR_model.py", "FR": "FR_model.py"}[family]
    road_file = {"quarter": "quarter_road.py", "LR": "LR_road.py", "FR": "FR_road.py"}[family]
    files = [
        HERE / "model" / model_file, HERE / "road" / road_file,
        HERE / "Parameter_set" / "Suspension.py",
        HERE / "Parameter_set" / "suspension_state.py",
    ]
    return {str(p.relative_to(HERE)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def prepare_case(family, model, scenario, dt=DEFAULT_DT, seed=None, *, suspension=None):
    reason = compatibility_error(family, model, scenario)
    if reason:
        raise ValueError(reason)
    spec = FAMILIES[family]
    # Some existing constructors print debugging values.
    if suspension is None:
        with open(os.devnull, "w") as sink, redirect_stdout(sink):
            suspension = spec.suspension_factory()
    state = spec.state_factory(dt)
    condition = spec.scenarios[scenario]
    parameters = dict(condition.parameters)
    if condition.function is RandomRoad:
        if seed is not None:
            parameters["seed"] = seed
        road = condition.function(**parameters)
    else:
        if family == "FR" and scenario == "impulse_drive":
            parameters["l"] = suspension.l
        if family == "FR" and scenario == "accelerate":
            parameters["m"] = 2 * suspension.m_corner
        road = partial(condition.function, **parameters)
    config = {
        "schema_version": 1,
        "family": family, "model": model, "scenario": scenario,
        "dt": dt, "input_start_s": INPUT_START, "duration_s": SIMULATION_TIME,
        "model_function": spec.models[model].function.__name__,
        "input_function": condition.function.__name__,
        "input_parameters": parameters,
        "suspension_parameters": {
            key: value.item() if isinstance(value, np.generic) else value
            for key, value in vars(suspension).items()
        },
        "source_hashes": source_hashes(family),
    }
    return suspension, state, road, spec.models[model].function, config


def simulate_case(suspension, state, road, model, config):
    """Log the initial sample and the exact end point; inputs align with t."""
    logger = SimulationLogger()
    steps = int(round(config["duration_s"] / state.dt))
    with open(os.devnull, "w") as sink, redirect_stdout(sink), np.errstate(
        over="raise", invalid="raise", divide="raise"
    ):
        for i in range(steps + 1):
            # Assign grid times instead of accumulating floating-point drift.
            state.t = i * state.dt
            for name in ("left", "right", "front", "rear"):
                if hasattr(state, name):
                    getattr(state, name).t = state.t
            road(state)
            model(suspension, state)
            logger.add_state(state)
            if i < steps:
                state.Integration(suspension)
    for key, values in logger.result().items():
        if not np.isfinite(values).all():
            raise FloatingPointError(f"Non-finite {key}: model may be numerically unstable")
    logger.set_metadata(
        config=config, created_utc=datetime.now(timezone.utc).isoformat(),
        time_convention="input and model evaluated at t; initial and final samples included",
    )
    return logger


def write_manifest(root, manifest):
    temp = root / "manifest.partial.json"
    temp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    temp.replace(root / "manifest.json")
    columns = ["family", "model", "scenario", "status", "pkl", "error"]
    with (root / "summary.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(manifest["cases"])


def main(families=None):
    families = list(families or FAMILIES)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", help="Optional model-name filter")
    parser.add_argument("--scenarios", nargs="+", help="Optional input-name filter")
    parser.add_argument("--output", type=Path, help="Output directory; default: data/results/suspension_batch")
    parser.add_argument("--dt", type=float, default=DEFAULT_DT)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--list", action="store_true", help="Show compatible cases without running")
    parser.add_argument("--resume", action="store_true", help="Reuse matching saved PKL data")
    args = parser.parse_args()
    if not np.isfinite(args.dt) or args.dt <= 0:
        parser.error("dt must be positive and finite")
    if not all(np.isclose(t / args.dt, round(t / args.dt), rtol=0, atol=1e-8)
               for t in (INPUT_START, SIMULATION_TIME)):
        parser.error("dt must divide both 0.25 s and 2 s exactly")
    try:
        cases, skipped = build_plan(families, args.models, args.scenarios)
    except ValueError as exc:
        parser.error(str(exc))
    if args.list:
        for case in cases:
            print(" / ".join(case.values()))
        for case in skipped:
            print(f"SKIP {case['family']}/{case['model']}/{case['scenario']}: {case['reason']}")
        print(f"{len(cases)} compatible cases; {len(skipped)} incompatible cases excluded")
        return 0

    root = (args.output or DEFAULT_OUTPUT).resolve()
    resume = args.resume
    root.mkdir(parents=True, exist_ok=True)
    manifest = {"input_start_s": INPUT_START, "duration_s": SIMULATION_TIME,
                "dt": args.dt,
                "skipped_incompatible": skipped, "cases": []}
    # Preserve only current, unselected cases in the shared output directory.
    previous = root / "manifest.json"
    if previous.exists():
        old = json.loads(previous.read_text(encoding="utf-8"))
        current_cases, current_skipped = build_plan(FAMILIES)
        valid = {(c["family"], c["model"], c["scenario"]) for c in current_cases}
        incompatible = {(c["family"], c["model"], c["scenario"]) for c in current_skipped}
        selected = {(c["family"], c["model"], c["scenario"]) for c in cases}
        manifest["cases"] = [{key: value for key, value in c.items() if key != "gif"}
                             for c in old.get("cases", [])
                             if (c["family"], c["model"], c["scenario"]) in valid - selected]
        seen = {(c["family"], c["model"], c["scenario"]) for c in skipped}
        manifest["skipped_incompatible"].extend(
            c for c in old.get("skipped_incompatible", [])
            if (c["family"], c["model"], c["scenario"]) in incompatible - seen
        )
    print(f"Output: {root}\nCases: {len(cases)}, excluded incompatible: {len(skipped)}", flush=True)
    failures = 0
    for index, case in enumerate(cases, 1):
        directory = root / case["family"] / case["model"] / case["scenario"]
        directory.mkdir(parents=True, exist_ok=True)
        pkl = directory / "result.pkl"
        row = {**case, "status": "pending", "pkl": "", "error": ""}
        manifest["cases"].append(row)
        print(f"[{index}/{len(cases)}] {case['family']}/{case['model']}/{case['scenario']}", flush=True)
        try:
            sus, state, road, model, config = prepare_case(**case, dt=args.dt, seed=args.seed)
            if resume and pkl.exists():
                logger = SimulationLogger.load(pkl)
                if logger.metadata.get("config") != config:
                    raise ValueError("Saved configuration/source differs; select a new --output directory")
            else:
                logger = simulate_case(sus, state, road, model, config)
                temp = pkl.with_suffix(".partial.pkl")
                logger.save(temp)
                temp.replace(pkl)
            row["pkl"] = pkl.relative_to(root).as_posix()
            row["status"] = "complete"
            (directory / "error.txt").unlink(missing_ok=True)
        except Exception as exc:
            failures += 1
            row["status"] = "failed"
            row["error"] = f"{type(exc).__name__}: {exc}"
            (directory / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
            print(f"  FAILED: {row['error']}", flush=True)
        write_manifest(root, manifest)
    print(f"Finished {len(cases)} cases; {failures} failed. Summary: {root / 'summary.csv'}", flush=True)
    return 1 if failures else 0


