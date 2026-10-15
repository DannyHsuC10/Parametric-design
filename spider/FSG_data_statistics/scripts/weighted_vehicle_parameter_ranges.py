#!/usr/bin/env python3
"""Compute rank-weighted vehicle parameter ranges from joined FSG data.

The input is expected to be fsg_results_vehicle_year_intersection.csv, produced
by extract_fsg_result_vehicle_intersections.py. Each row is one historical
result with same-team same-year vehicle specs appended as vehicle_* columns.

Rows are first aggregated to one sample per team-year so teams that enter more
events in the same year do not receive extra statistical weight. By default,
the annual weight uses the team's best event rank in that year and a recency
factor so older seasons count less:

    weight = (1 / rank) * (1 / (1 + latest_year - sample_year))

The script estimates a weighted normal distribution for each numeric vehicle
parameter and writes mean +/- 3 weighted standard deviations.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


SCRIPT_DIR = Path(__file__).resolve().parent
DATA_ROOT = SCRIPT_DIR.parent
COMPUTED_DIR = DATA_ROOT / "computed_statistics"


DEFAULT_INPUT_CSV = COMPUTED_DIR / "fsg_results_vehicle_year_intersection.csv"
DEFAULT_OUTPUT_CSV = COMPUTED_DIR / "fsg_weighted_vehicle_parameter_ranges.csv"


@dataclass(frozen=True)
class Parameter:
    name: str
    columns: tuple[str, ...]
    unit: str
    parser: Callable[[dict[str, str], "Parameter"], float | None]
    min_valid: float | None = None
    max_valid: float | None = None


def clean_number_token(token: str) -> float | None:
    token = token.strip()
    if not token:
        return None

    if "," in token and "." in token:
        normalized = token.replace(",", "")
    elif "," in token:
        left, right = token.split(",", 1)
        if len(right) == 3 and 1 <= len(left) <= 3:
            normalized = left + right
        else:
            normalized = left + "." + right
    elif "." in token:
        left, right = token.split(".", 1)
        if len(right) == 3 and 1 <= len(left) <= 3:
            as_decimal = float(left + "." + right)
            as_thousands = float(left + right)
            return as_thousands if as_decimal < 100 else as_decimal
        normalized = token
    else:
        normalized = token

    try:
        return float(normalized)
    except ValueError:
        return None


def number_tokens(value: str) -> list[float]:
    text = (value or "").strip()
    if not text or text in {"-", "n/a", "N/A"}:
        return []

    values: list[float] = []
    for match in re.finditer(r"-?\d+(?:[,.]\d+)?", text):
        number = clean_number_token(match.group(0))
        if number is not None:
            values.append(number)
    return values


def in_range(value: float, parameter: Parameter) -> bool:
    if parameter.min_valid is not None and value < parameter.min_valid:
        return False
    if parameter.max_valid is not None and value > parameter.max_valid:
        return False
    return True


def first_valid_number(row: dict[str, str], parameter: Parameter) -> float | None:
    for column in parameter.columns:
        for value in number_tokens(row.get(column, "")):
            if in_range(value, parameter):
                return value
    return None


def max_valid_number(row: dict[str, str], parameter: Parameter) -> float | None:
    for column in parameter.columns:
        values = [value for value in number_tokens(row.get(column, "")) if in_range(value, parameter)]
        if values:
            return max(values)
    return None


def last_valid_number(row: dict[str, str], parameter: Parameter) -> float | None:
    for column in parameter.columns:
        values = [value for value in number_tokens(row.get(column, "")) if in_range(value, parameter)]
        if values:
            return values[-1]
    return None


FIELD_VALID_RANGES = {
    "vehicle_Track (Fr)": (700, 2000),
    "vehicle_Track (Rr)": (700, 2000),
    "vehicle_Weight with 68kg driver (Fr)": (40, 350),
    "vehicle_Weight with 68kg driver (Rr)": (40, 350),
}


def first_valid_number_for_column(row: dict[str, str], column: str) -> float | None:
    min_valid, max_valid = FIELD_VALID_RANGES.get(column, (None, None))
    column_param = Parameter(column, (column,), "", first_valid_number, min_valid, max_valid)
    return first_valid_number(row, column_param)


def sum_columns(row: dict[str, str], parameter: Parameter) -> float | None:
    values: list[float] = []
    for column in parameter.columns:
        value = first_valid_number_for_column(row, column)
        if value is None:
            return None
        values.append(value)
    total = sum(values)
    return total if in_range(total, parameter) else None


def ratio_columns(row: dict[str, str], parameter: Parameter) -> float | None:
    if len(parameter.columns) != 2:
        return None

    left = first_valid_number_for_column(row, parameter.columns[0])
    right = first_valid_number_for_column(row, parameter.columns[1])
    if left is None or right in (None, 0):
        return None
    ratio = left / right
    return ratio if in_range(ratio, parameter) else None


PARAMETERS: tuple[Parameter, ...] = (
    Parameter("Overall length", ("vehicle_Overall L",), "mm", first_valid_number, 1000, 4000),
    Parameter("Overall width", ("vehicle_Overall W",), "mm", first_valid_number, 800, 2500),
    Parameter("Overall height", ("vehicle_Overall H",), "mm", first_valid_number, 500, 2500),
    Parameter("Wheelbase", ("vehicle_Wheelbase",), "mm", first_valid_number, 1000, 3000),
    Parameter("Front track", ("vehicle_Track (Fr)",), "mm", first_valid_number, 700, 2000),
    Parameter("Rear track", ("vehicle_Track (Rr)",), "mm", first_valid_number, 700, 2000),
    Parameter("Front/rear track ratio", ("vehicle_Track (Fr)", "vehicle_Track (Rr)"), "ratio", ratio_columns, 0.75, 1.35),
    Parameter("Front weight with driver", ("vehicle_Weight with 68kg driver (Fr)",), "kg", first_valid_number, 40, 350),
    Parameter("Rear weight with driver", ("vehicle_Weight with 68kg driver (Rr)",), "kg", first_valid_number, 40, 350),
    Parameter(
        "Total weight with driver",
        ("vehicle_Weight with 68kg driver (Fr)", "vehicle_Weight with 68kg driver (Rr)"),
        "kg",
        sum_columns,
        150,
        700,
    ),
    Parameter(
        "Front/rear weight ratio",
        ("vehicle_Weight with 68kg driver (Fr)", "vehicle_Weight with 68kg driver (Rr)"),
        "ratio",
        ratio_columns,
        0.3,
        2.5,
    ),
    Parameter("Number of motors", ("vehicle_Number of Motors",), "count", first_valid_number, 1, 8),
    Parameter("Max motor power per motor", ("vehicle_Max Motor Power (per motor)",), "kW", max_valid_number, 5, 300),
    Parameter("Max motor RPM", ("vehicle_Max Motor RPM (highest)",), "rpm", first_valid_number, 1000, 50000),
    Parameter("Max system voltage", ("vehicle_Max System Voltage",), "V", first_valid_number, 20, 900),
    Parameter("Accumulator capacity", ("vehicle_Combined Accumulator Capacity",), "kWh", first_valid_number, 0.5, 20),
    Parameter(
        "DV processing performance",
        ("vehicle_Floating Point Operations Per Second of all processing units that are working for the DV system",),
        "GigaFLOPS",
        last_valid_number,
        1,
        20000,
    ),
    Parameter(
        "DV processing power consumption",
        ("vehicle_Power consumption of all processing units that are working for the DV system",),
        "W",
        first_valid_number,
        1,
        2000,
    ),
    Parameter("Engine bore", ("vehicle_Bore",), "mm", first_valid_number, 10, 150),
    Parameter("Engine stroke", ("vehicle_Stroke",), "mm", first_valid_number, 10, 150),
    Parameter("Cylinders", ("vehicle_Cylinders",), "count", first_valid_number, 1, 8),
    Parameter("Displacement", ("vehicle_Displacement",), "cc", first_valid_number, 50, 1500),
    Parameter("Compression ratio", ("vehicle_Compression Ratio",), "ratio", first_valid_number, 5, 20),
    Parameter("Max power design", ("vehicle_Max Power Design",), "kW", first_valid_number, 1, 300),
    Parameter("Max torque design", ("vehicle_Max Torque Design",), "Nm", first_valid_number, 1, 500),
)


def parse_rank(value: str) -> float | None:
    values = number_tokens(value)
    if not values:
        return None
    rank = values[0]
    return rank if rank > 0 else None


def extract_year(value: str) -> str:
    match = re.search(r"(19|20)\d{2}", value or "")
    return match.group(0) if match else ""


def annual_sample_key(row: dict[str, str]) -> tuple[str, str] | None:
    team = re.sub(r"\s+", " ", row.get("team", "").strip()).casefold()
    year = extract_year(row.get("match_year", "")) or extract_year(row.get("date", ""))
    if not team or not year:
        return None
    return team, year


def rank_weight(rank: float | None, mode: str) -> float | None:
    if rank is None:
        return None

    if mode == "inverse_rank":
        return 1.0 / rank
    if mode == "inverse_sqrt_rank":
        return 1.0 / math.sqrt(rank)
    if mode == "rank":
        return rank
    if mode == "equal":
        return 1.0
    raise ValueError(f"Unsupported weight mode: {mode}")


def year_weight(year: int | None, latest_year: int | None, mode: str) -> float:
    if year is None or latest_year is None:
        return 1.0

    age = max(0, latest_year - year)
    if mode == "recency_inverse_age":
        return 1.0 / (1.0 + age)
    if mode == "recency_exp_5":
        return 0.5 ** (age / 5.0)
    if mode == "equal":
        return 1.0
    raise ValueError(f"Unsupported year weight mode: {mode}")


def annual_parameter_samples(
    rows: list[dict[str, str]],
    parameter: Parameter,
    weight_mode: str,
    year_weight_mode: str,
) -> list[tuple[float, float, float, float]]:
    grouped: dict[tuple[str, str], dict[str, list[float] | float | int]] = {}

    for row in rows:
        key = annual_sample_key(row)
        rank = parse_rank(row.get("place", ""))
        if key is None or rank is None:
            continue

        value = parameter.parser(row, parameter)
        if value is None or not in_range(value, parameter):
            continue

        entry = grouped.setdefault(key, {"values": [], "best_rank": rank, "year": int(key[1])})
        entry["values"].append(value)  # type: ignore[index, union-attr]
        entry["best_rank"] = min(float(entry["best_rank"]), rank)

    latest_year = max((int(key[1]) for key in grouped), default=None)

    samples: list[tuple[float, float, float, float]] = []
    for entry in grouped.values():
        values = entry["values"]
        if not isinstance(values, list) or not values:
            continue
        annual_value = sum(values) / len(values)
        best_rank = float(entry["best_rank"])
        sample_year = int(entry["year"])
        rank_factor = rank_weight(best_rank, weight_mode)
        year_factor = year_weight(sample_year, latest_year, year_weight_mode)
        weight = None if rank_factor is None else rank_factor * year_factor
        if weight is not None and weight > 0:
            samples.append((annual_value, weight, best_rank, year_factor))

    return samples


def weighted_stats(values: list[tuple[float, float]]) -> tuple[float, float, float]:
    total_weight = sum(weight for _, weight in values)
    if total_weight <= 0:
        return math.nan, math.nan, 0.0

    mean = sum(value * weight for value, weight in values) / total_weight
    variance = sum(weight * (value - mean) ** 2 for value, weight in values) / total_weight
    return mean, math.sqrt(max(variance, 0.0)), total_weight


def format_number(value: float) -> str:
    if math.isnan(value):
        return ""
    if abs(value) >= 100:
        return f"{value:.2f}"
    return f"{value:.4f}".rstrip("0").rstrip(".")


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "parameter",
        "unit",
        "sample_count",
        "weighted_sample_count",
        "weighted_mean",
        "weighted_std",
        "lower_3sigma",
        "upper_3sigma",
        "recommended_lower",
        "recommended_upper",
        "observed_min",
        "observed_max",
        "rank_weight_mode",
        "year_weight_mode",
        "weight_basis",
        "source_columns",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def compute_ranges(
    rows: list[dict[str, str]],
    weight_mode: str,
    year_weight_mode: str,
    min_samples: int,
) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []

    for parameter in PARAMETERS:
        samples = annual_parameter_samples(rows, parameter, weight_mode, year_weight_mode)
        values = [(value, weight) for value, weight, _, _ in samples]

        if len(values) < min_samples:
            continue

        raw_values = [value for value, _ in values]
        mean, std, total_weight = weighted_stats(values)
        lower_3sigma = mean - 3 * std
        upper_3sigma = mean + 3 * std
        recommended_lower = lower_3sigma
        recommended_upper = upper_3sigma
        if parameter.min_valid is not None:
            recommended_lower = max(recommended_lower, parameter.min_valid)
        if parameter.max_valid is not None:
            recommended_upper = min(recommended_upper, parameter.max_valid)

        output.append(
            {
                "parameter": parameter.name,
                "unit": parameter.unit,
                "sample_count": str(len(values)),
                "weighted_sample_count": format_number(total_weight),
                "weighted_mean": format_number(mean),
                "weighted_std": format_number(std),
                "lower_3sigma": format_number(lower_3sigma),
                "upper_3sigma": format_number(upper_3sigma),
                "recommended_lower": format_number(recommended_lower),
                "recommended_upper": format_number(recommended_upper),
                "observed_min": format_number(min(raw_values)),
                "observed_max": format_number(max(raw_values)),
                "rank_weight_mode": weight_mode,
                "year_weight_mode": year_weight_mode,
                "weight_basis": "one sample per team-year, annual best place x recency year weight",
                "source_columns": " + ".join(parameter.columns),
            }
        )

    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute rank-weighted mean/std and 3-sigma ranges for numeric vehicle parameters."
    )
    parser.add_argument("--input", default=DEFAULT_INPUT_CSV, help="Joined result + vehicle CSV path.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_CSV, help="Output statistics CSV path.")
    parser.add_argument(
        "--weight-mode",
        choices=("inverse_rank", "inverse_sqrt_rank", "rank", "equal"),
        default="inverse_rank",
        help="How to convert rank/place to statistical weight. Default: inverse_rank.",
    )
    parser.add_argument(
        "--year-weight-mode",
        choices=("recency_inverse_age", "recency_exp_5", "equal"),
        default="recency_inverse_age",
        help="How to weight older seasons. Default: recency_inverse_age.",
    )
    parser.add_argument("--min-samples", type=int, default=5, help="Minimum numeric samples required per parameter.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    rows = read_rows(input_path)
    stats = compute_ranges(rows, args.weight_mode, args.year_weight_mode, args.min_samples)
    write_rows(output_path, stats)

    print(f"Input rows: {len(rows)}")
    print(f"Parameters exported: {len(stats)}")
    print(f"Weight mode: {args.weight_mode}")
    print(f"Year weight mode: {args.year_weight_mode}")
    print("Weight basis: one sample per team-year, annual best place x recency year weight")
    print(f"Output CSV: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
