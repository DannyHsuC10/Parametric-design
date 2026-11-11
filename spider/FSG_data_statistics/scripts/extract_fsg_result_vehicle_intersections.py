#!/usr/bin/env python3
"""Extract rows where FSG/FSE results and vehicle specs share team + year.

The default output keeps each historical result row and appends the matching
vehicle fields from FSG_EV_vehicle_database.csv. Matching is based on normalized
team name and year:

    fse_historical_results.csv: year = first 4 digits of the date column
    FSG_EV_vehicle_database.csv: year = year column
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DATA_ROOT = SCRIPT_DIR.parent
RAW_DATA_DIR = DATA_ROOT / "raw_data"
COMPUTED_DIR = DATA_ROOT / "computed_statistics"


DEFAULT_RESULTS_CSV = RAW_DATA_DIR / "fse_historical_results.csv"
DEFAULT_VEHICLES_CSV = RAW_DATA_DIR / "FSG_EV_vehicle_database.csv"
DEFAULT_OUTPUT_CSV = COMPUTED_DIR / "fsg_results_vehicle_year_intersection.csv"


def normalize_team(value: str) -> str:
    """Normalize a team name enough for CSV-to-CSV matching."""
    return re.sub(r"\s+", " ", (value or "").strip()).casefold()


def extract_year_from_date(value: str) -> str:
    match = re.search(r"(19|20)\d{2}", value or "")
    return match.group(0) if match else ""


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def prefixed_fields(prefix: str, fields: list[str], skip: set[str]) -> list[str]:
    return [f"{prefix}{field}" for field in fields if field not in skip]


def build_vehicle_index(
    rows: list[dict[str, str]],
) -> tuple[dict[tuple[str, str], list[dict[str, str]]], Counter]:
    index: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    invalid_years: Counter = Counter()

    for row in rows:
        team_key = normalize_team(row.get("team", ""))
        year = extract_year_from_date(row.get("year", ""))
        if not team_key or not year:
            invalid_years["vehicle_rows_without_team_or_year"] += 1
            continue
        index[(team_key, year)].append(row)

    duplicate_keys = Counter(
        {f"{team}|{year}": len(matches) for (team, year), matches in index.items() if len(matches) > 1}
    )
    return dict(index), invalid_years + Counter({"duplicate_vehicle_team_year_keys": len(duplicate_keys)})


def join_rows(
    result_fields: list[str],
    vehicle_fields: list[str],
    result_rows: list[dict[str, str]],
    vehicle_index: dict[tuple[str, str], list[dict[str, str]]],
) -> tuple[list[str], list[dict[str, str]], Counter]:
    skip_vehicle_fields = {"team", "year"}
    output_fields = (
        ["match_year"]
        + result_fields
        + prefixed_fields("vehicle_", vehicle_fields, skip_vehicle_fields)
    )

    output_rows: list[dict[str, str]] = []
    stats: Counter = Counter()

    for result in result_rows:
        team_key = normalize_team(result.get("team", ""))
        year = extract_year_from_date(result.get("date", ""))
        if not team_key or not year:
            stats["result_rows_without_team_or_year"] += 1
            continue

        matches = vehicle_index.get((team_key, year), [])
        if not matches:
            stats["result_rows_without_vehicle_match"] += 1
            continue

        if len(matches) > 1:
            stats["result_rows_with_multiple_vehicle_matches"] += 1

        for vehicle in matches:
            joined = {field: "" for field in output_fields}
            joined["match_year"] = year

            for field in result_fields:
                joined[field] = result.get(field, "")

            for field in vehicle_fields:
                if field in skip_vehicle_fields:
                    continue
                joined[f"vehicle_{field}"] = vehicle.get(field, "")

            output_rows.append(joined)
            stats["matched_output_rows"] += 1

    return output_fields, output_rows, stats


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Join FSG/FSE historical results with same-team same-year vehicle parameters."
    )
    parser.add_argument("--results", default=DEFAULT_RESULTS_CSV, help="Historical results CSV path.")
    parser.add_argument("--vehicles", default=DEFAULT_VEHICLES_CSV, help="Vehicle parameter CSV path.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_CSV, help="Output CSV path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results_path = Path(args.results)
    vehicles_path = Path(args.vehicles)
    output_path = Path(args.output)

    result_fields, result_rows = read_csv(results_path)
    vehicle_fields, vehicle_rows = read_csv(vehicles_path)
    vehicle_index, index_stats = build_vehicle_index(vehicle_rows)
    output_fields, output_rows, join_stats = join_rows(
        result_fields,
        vehicle_fields,
        result_rows,
        vehicle_index,
    )
    write_csv(output_path, output_fields, output_rows)

    matched_keys = {
        (normalize_team(row.get("team", "")), extract_year_from_date(row.get("date", "")))
        for row in result_rows
        if normalize_team(row.get("team", "")) and extract_year_from_date(row.get("date", ""))
    } & set(vehicle_index)

    print(f"Results rows: {len(result_rows)}")
    print(f"Vehicle rows: {len(vehicle_rows)}")
    print(f"Matched team-year keys: {len(matched_keys)}")
    print(f"Output rows: {len(output_rows)}")
    print(f"Output CSV: {output_path}")

    for key, value in sorted((index_stats + join_stats).items()):
        if value:
            print(f"{key}: {value}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
