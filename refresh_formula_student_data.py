#!/usr/bin/env python3
"""Refresh the three Formula Student CSVs bundled with the website."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import sys
import tempfile
import time
from collections import defaultdict
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen


DATA_DIR = Path(__file__).resolve().parent / "web" / "formula-student" / "data"
VEHICLE_CSV = "FSG_EV_vehicle_database.csv"
RESULTS_CSV = "fse_historical_results.csv"
MATCHED_CSV = "fsg_results_vehicle_year_intersection.csv"
METADATA_JSON = "crawl_metadata.json"
TEAM_LIST_URL = "https://www.formulastudent.de/teams/fse"
TEAM_PATH = re.compile(r"/teams/fse/details/tid/(\d+)/?")
TEAM_URL = TEAM_LIST_URL + "/details/tid/{}"
REQUEST_INTERVAL = 0.5
CAR_CARD = re.compile(r'<div\b[^>]*\bclass="(?:[^"]*\s)?timeline-card(?:\s[^"]*)?"[^>]*>', re.I)
RESULT_YEAR = re.compile(r"^((?:19|20)\d{2})(?=\D|$)")
TEAM_DETAILS = re.compile(r"<h1\b[^>]*>\s*Team Details\s*</h1>", re.I)

VEHICLE_FIELDS = (
    "team", "team_id", "year", "car_title",
    "Frame Construction", "Material", "Overall L", "Overall W", "Overall H",
    "Wheelbase", "Track (Fr)", "Track (Rr)",
    "Weight with 68kg driver (Fr)", "Weight with 68kg driver (Rr)",
    "Suspension", "Tyres (Fr / Rr)", "Wheels (Fr / Rr)", "Drive Type",
    "Differential", "Cooling", "Brake System", "Electronics",
    "Number of Motors", "Motor Location", "Max Motor Power (per motor)",
    "Motor Type", "Max Motor RPM (highest)", "Motor Controller",
    "Max System Voltage", "Electrode Materials", "Combined Accumulator Capacity",
    "Transmission Ratio (Primary)", "Transmission Ratio (Secondary)",
    "Processing unit(s)",
    "Floating Point Operations Per Second of all processing units that are working for the DV system",
    "Power consumption of all processing units that are working for the DV system",
    "Camera(s)", "Radar sensor(s)", "Lidar sensor(s)", "Other sensors",
    "Highlights of the DV system", "Engine", "Bore", "Stroke", "Cylinders",
    "Displacement", "Compression Ratio", "Fuel System", "Fuel",
    "Max Power Design", "Max Torque Design",
)
CAR_SPEC_FIELDS = frozenset(VEHICLE_FIELDS[4:])
RESULT_FIELDS = (
    "team", "team_url", "date", "event", "class", "teams_count", "place",
    "cost", "business_plan", "engineering_design", "acceleration", "skidpad",
    "autocross", "endurance", "fuel_efficiency", "penalties", "total_score",
    "world_ranking",
)
RESULT_HEADINGS = {
    "date": "date", "event": "event", "c": "class", "class": "class",
    "teams": "teams_count", "# teams": "teams_count", "participants": "teams_count",
    "rank": "place", "place": "place", "placing": "place",
    "cm": "cost", "cost": "cost",
    "bp": "business_plan", "business plan": "business_plan",
    "ed": "engineering_design", "engineering design": "engineering_design",
    "ac": "acceleration", "acc": "acceleration", "acceleration": "acceleration",
    "sp": "skidpad", "skidpad": "skidpad",
    "ax": "autocross", "autox": "autocross", "autocross": "autocross",
    "en": "endurance", "endu": "endurance", "endurance": "endurance",
    "ef": "fuel_efficiency", "fuel": "fuel_efficiency", "efficiency": "fuel_efficiency",
    "pe": "penalties", "pen": "penalties", "penalties": "penalties",
    "total": "total_score", "total score": "total_score",
    "wrl": "world_ranking", "world ranking": "world_ranking",
}
MATCHED_VEHICLE_FIELDS = tuple(field for field in VEHICLE_FIELDS if field not in {"team", "year"})
MATCHED_FIELDS = (
    "match_year", *RESULT_FIELDS, *(f"vehicle_{field}" for field in MATCHED_VEHICLE_FIELDS),
)


class PageParser(HTMLParser):
    """Read link labels and table cells from the FSG pages."""

    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self.rows: list[list[str]] = []
        self._href: str | None = None
        self._link_text: list[str] = []
        self._table_depth = 0
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._link_text = []
        elif tag == "table":
            self._table_depth += 1
        elif tag == "tr" and self._table_depth:
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            self.links.append((self._href, self.clean(self._link_text)))
            self._href = None
        elif tag in {"td", "th"} and self._cell is not None and self._row is not None:
            self._row.append(self.clean(self._cell))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None
        elif tag == "table":
            self._table_depth -= 1

    def handle_data(self, data):
        if self._href is not None:
            self._link_text.append(data)
        if self._cell is not None:
            self._cell.append(data)

    @staticmethod
    def clean(parts):
        return " ".join(" ".join(parts).split())


def parse_page(html: str) -> PageParser:
    parser = PageParser()
    parser.feed(html)
    parser.close()
    return parser


def team_id_from_url(url: str) -> str | None:
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.netloc not in {"www.formulastudent.de", "formulastudent.de"}:
        return None
    match = TEAM_PATH.fullmatch(parts.path)
    return match.group(1) if match else None


def parse_teams(html: str) -> dict[str, str]:
    teams = {}
    for href, name in parse_page(html).links:
        team_id = team_id_from_url(urljoin(TEAM_LIST_URL, href))
        if team_id and name:
            teams.setdefault(team_id, name)
    if not teams:
        raise ValueError("The FSG team list contained no FSE team links.")
    return teams


def fetch_html(url: str) -> str:
    request = Request(url, headers={"User-Agent": "VehicleInitialSizingLab/1.0 (Formula Student data refresh)"})
    for attempt in range(2):
        try:
            with urlopen(request, timeout=30) as response:
                return response.read().decode(response.headers.get_content_charset() or "utf-8", errors="replace")
        except (OSError, HTTPException) as error:
            retryable = not isinstance(error, HTTPError) or error.code in {500, 502, 503, 504}
            if attempt or not retryable:
                raise RuntimeError(f"Could not read {url}: {error}") from error
            time.sleep(2)


def car_title(card: str) -> str:
    parts = []
    for css_class in ("car-number-small", "car-name-small"):
        match = re.search(rf'class="[^"]*\b{css_class}\b[^"]*"[^>]*>(.*?)</span>', card, re.I | re.S)
        if match:
            text = unescape(re.sub(r"<[^>]+>", " ", match.group(1)))
            parts.append(" ".join(text.split()))
    return " ".join(part for part in parts if part)


def parse_vehicles(html: str, team_id: str, team_name: str) -> list[dict[str, str]]:
    cards = list(CAR_CARD.finditer(html))
    cars = []
    seen = set()
    for index, opening in enumerate(cards):
        year = re.search(r'data-year="((?:19|20)\d{2})"', opening.group())
        end = cards[index + 1].start() if index + 1 < len(cards) else len(html)
        card = re.split(r"FS past achievements|fs-past-achievements", html[opening.end():end], maxsplit=1, flags=re.I)[0]
        if not year or "Car Specifications" not in card:
            continue
        specs = {}
        for cells in parse_page(card.split("Car Specifications", 1)[1]).rows:
            if len(cells) >= 2:
                key = cells[0].replace("*", "").strip()
                if key in CAR_SPEC_FIELDS:
                    specs[key] = cells[1]
        if not any(specs.values()):
            continue
        title = car_title(card)
        key = (year.group(1), title)
        if key not in seen:
            seen.add(key)
            cars.append({"team": team_name, "team_id": team_id, "year": key[0], "car_title": title, **specs})
    return cars


def parse_results(html: str, team_url: str, team_name: str) -> list[dict[str, str]]:
    results = []
    columns = []
    for cells in parse_page(html).rows:
        if [cell.casefold() for cell in cells[:2]] == ["date", "event"]:
            headings = [RESULT_HEADINGS.get(cell.casefold()) for cell in cells]
            columns = headings if "place" in headings else []
            continue
        if columns and len(cells) >= len(columns) and RESULT_YEAR.match(cells[0]) and cells[1]:
            result = {field: value for field, value in zip(columns, cells) if field is not None}
            results.append({"team": team_name, "team_url": team_url, **result})
    return results


def read_existing_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def match_results(vehicles: list[dict[str, str]], results: list[dict[str, str]]) -> list[dict[str, str]]:
    cars_by_team_year = defaultdict(list)
    for car in vehicles:
        cars_by_team_year[(car["team_id"], car["year"])].append(car)

    matched = []
    for result in results:
        year = RESULT_YEAR.match(result["date"])
        team_id = team_id_from_url(result["team_url"])
        if year and team_id:
            for car in cars_by_team_year.get((team_id, year.group(1)), []):
                spec = {f"vehicle_{field}": car.get(field, "") for field in MATCHED_VEHICLE_FIELDS}
                matched.append({"match_year": year.group(1), **result, **spec})
    return matched


def write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def publish_snapshot(staged: Path, data_dir: Path, filenames: tuple[str, ...]) -> None:
    backup = staged / "previous"
    backup.mkdir()
    for filename in filenames:
        current = data_dir / filename
        if current.exists():
            shutil.copy2(current, backup / filename)

    replaced = []
    try:
        for filename in filenames:
            os.replace(staged / filename, data_dir / filename)
            replaced.append(filename)
    except (OSError, KeyboardInterrupt):
        for filename in reversed(replaced):
            previous = backup / filename
            if previous.exists():
                os.replace(previous, data_dir / filename)
            else:
                (data_dir / filename).unlink()
        raise


def refresh(data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    lock = data_dir / ".refresh.lock"
    try:
        lock.touch(exist_ok=False)
    except FileExistsError as error:
        raise RuntimeError(f"An update already holds {lock}.") from error

    try:
        teams = parse_teams(fetch_html(TEAM_LIST_URL))
        print(f"Found {len(teams)} FSE teams. Fetching each team page once.", flush=True)
        vehicles = []
        results = []
        for number, (team_id, team_name) in enumerate(teams.items(), start=1):
            time.sleep(REQUEST_INTERVAL)
            url = TEAM_URL.format(team_id)
            html = fetch_html(url)
            team_vehicles = parse_vehicles(html, team_id, team_name)
            team_results = parse_results(html, url, team_name)
            if not (team_vehicles or team_results or TEAM_DETAILS.search(html)):
                raise ValueError(f"FSG did not return a team detail page for team {team_id}.")
            vehicles.extend(team_vehicles)
            results.extend(team_results)
            if number % 20 == 0 or number == len(teams):
                print(f"Processed {number}/{len(teams)} teams.", flush=True)

        if not any(re.search(r"\d", car.get("Wheelbase", "")) for car in vehicles):
            raise ValueError("No vehicle records with a usable wheelbase were found.")
        if not any(re.search(r"\d", result.get("place", "")) for result in results):
            raise ValueError("No FSE results with a usable rank were found.")

        # Preserve historical records from teams that no longer appear in the FSE directory.
        vehicles.extend(row for row in read_existing_csv(data_dir / VEHICLE_CSV) if row["team_id"] not in teams)
        results.extend(row for row in read_existing_csv(data_dir / RESULTS_CSV) if team_id_from_url(row["team_url"]) not in teams)
        vehicles.sort(key=lambda car: (car["team"].casefold(), car["year"], car["car_title"]))
        matched = match_results(vehicles, results)
        wheelbase_samples = {
            (" ".join(row["team"].lower().split()), row["match_year"])
            for row in matched
            if re.search(r"\d", row["vehicle_Wheelbase"]) and re.match(r"[1-9]\d*", row.get("place", ""))
        }
        # The distribution page needs five team-year samples to show statistics.
        if len(wheelbase_samples) < 5:
            raise ValueError("Fewer than five ranked team-years have matching wheelbase data.")

        with tempfile.TemporaryDirectory(dir=data_dir, prefix=".refresh-") as folder:
            staged = Path(folder)
            write_csv(staged / VEHICLE_CSV, VEHICLE_FIELDS, vehicles)
            write_csv(staged / RESULTS_CSV, RESULT_FIELDS, results)
            write_csv(staged / MATCHED_CSV, MATCHED_FIELDS, matched)
            updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            (staged / METADATA_JSON).write_text(
                json.dumps({"last_successful_crawl": updated_at}, indent=2) + "\n", encoding="utf-8",
            )
            publish_snapshot(staged, data_dir, (VEHICLE_CSV, RESULTS_CSV, MATCHED_CSV, METADATA_JSON))
        print(f"Updated {data_dir}")
        print(f"{len(vehicles)} vehicle records, {len(results)} FSE results, {len(matched)} matched rows.")
        print(f"Last successful crawl: {updated_at}")
    finally:
        lock.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DATA_DIR, help="Directory for the CSVs and crawl timestamp.")
    args = parser.parse_args()
    try:
        refresh(args.output_dir.resolve())
    except KeyboardInterrupt:
        print("\nUpdate canceled.", file=sys.stderr)
        return 130
    except (OSError, RuntimeError, ValueError, KeyError, csv.Error) as error:
        print(f"Update failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
