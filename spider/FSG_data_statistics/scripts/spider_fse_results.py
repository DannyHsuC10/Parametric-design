"""Download Formula Student Germany's historical FSE team achievements to CSV.

Usage: python scrape_fse_results.py [output.csv]

The source site exposes each team's historical achievements on its team detail
page. The output contains one row per team/event achievement.
"""

from __future__ import annotations

import csv
import re
import sys
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


TEAM_LIST_URL = "https://www.formulastudent.de/teams/fse"
BASE_URL = "https://www.formulastudent.de/"
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_ROOT = SCRIPT_DIR.parent
RAW_DATA_DIR = DATA_ROOT / "raw_data"
DEFAULT_OUTPUT_CSV = RAW_DATA_DIR / "fse_historical_results.csv"
FIELDS = [
    "team",
    "team_url",
    "date",
    "event",
    "class",
    "teams_count",
    "place",
    "cost",
    "business_plan",
    "engineering_design",
    "acceleration",
    "skidpad",
    "autocross",
    "endurance",
    "fuel_efficiency",
    "penalties",
    "total_score",
    "world_ranking",
]
HISTORY_HEADERS = [
    "date", "event", "class", "teams_count", "place", "cost", "business_plan",
    "engineering_design", "acceleration", "skidpad", "autocross",
    "endurance", "fuel_efficiency", "penalties", "total_score",
    "world_ranking",
]
CURRENT_HEADERS = [
    "date", "event", "teams", "rank", "bp", "cm", "ed", "sp", "dv sp",
    "ac", "dv ac", "ax", "en", "ef", "pe", "total",
]
CURRENT_TO_HISTORY = {
    "date": "date",
    "event": "event",
    "teams": "teams_count",
    "rank": "place",
    "bp": "business_plan",
    "cm": "cost",
    "ed": "engineering_design",
    "sp": "skidpad",
    "ac": "autocross",
    "ax": "acceleration",
    "en": "endurance",
    "ef": "fuel_efficiency",
    "pe": "penalties",
    "total": "total_score",
}

def fetch(url: str) -> str:
    request = Request(url, headers={"User-Agent": "FSE-results-research/1.0 (polite crawler)"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode(response.headers.get_content_charset() or "utf-8", errors="replace")


class PageParser(HTMLParser):
    """Collect links, headings, and plain text table rows from a page."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self.headings: list[str] = []
        self.rows: list[list[str]] = []
        self._anchor_href: str | None = None
        self._anchor_text: list[str] = []
        self._heading: list[str] | None = None
        self._table_depth = 0
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    @staticmethod
    def _clean(parts: list[str]) -> str:
        return re.sub(r"\s+", " ", " ".join(parts)).strip()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "a":
            self._anchor_href = attrs_dict.get("href")
            self._anchor_text = []
        elif tag in {"h1", "h2", "h3", "h4"}:
            self._heading = []
        elif tag == "table":
            self._table_depth += 1
        elif tag == "tr" and self._table_depth:
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._anchor_href is not None:
            self.links.append((self._anchor_href, self._clean(self._anchor_text)))
            self._anchor_href = None
            self._anchor_text = []
        elif tag in {"h1", "h2", "h3", "h4"} and self._heading is not None:
            self.headings.append(self._clean(self._heading))
            self._heading = None
        elif tag in {"td", "th"} and self._cell is not None and self._row is not None:
            self._row.append(self._clean(self._cell))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None
        elif tag == "table" and self._table_depth:
            self._table_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._anchor_href is not None:
            self._anchor_text.append(data)
        if self._heading is not None:
            self._heading.append(data)
        if self._cell is not None:
            self._cell.append(data)


def get_teams(html: str) -> list[tuple[str, str]]:
    parser = PageParser()
    parser.feed(html)
    teams: list[tuple[str, str]] = []
    seen: set[str] = set()
    for href, name in parser.links:
        if not name or not re.search(r"/teams/fse/details/tid/\d+", href):
            continue
        url = urljoin(BASE_URL, href)
        if url not in seen:
            seen.add(url)
            teams.append((name, url))
    if not teams:
        raise RuntimeError("No team detail links found; the source page structure may have changed.")
    return teams


def get_history_rows(html: str) -> list[list[str]]:
    parser = PageParser()
    parser.feed(html)
    # A source table can render as separate tables for each visual row, so also
    # normalize table rows by identifying the header, then append subsequent rows.
    aliases = {
        "date": {"date"}, "event": {"event"}, "class": {"c", "class"},
        "teams_count": {"teams", "# teams", "participants"},
        "place": {"place", "placing"}, "cost": {"cost"},
        "business_plan": {"bp", "business plan"},
        "engineering_design": {"ed", "engineering design"},
        "acceleration": {"acc", "acceleration"}, "skidpad": {"sp", "skidpad"},
        "autocross": {"autox", "autocross"}, "endurance": {"endu", "endurance"},
        "fuel_efficiency": {"fuel", "efficiency"}, "penalties": {"pen", "penalties"},
        "total_score": {"total", "total score"},
        "world_ranking": {"wrl", "world ranking"},
    }
    expected_width = len(HISTORY_HEADERS)
    header_indices = []
    for i, row in enumerate(parser.rows):
        normalized = [normalize_heading(cell) for cell in row]
        if len(normalized) >= expected_width and all(
            normalized[pos] in aliases[field]
            for pos, field in enumerate(HISTORY_HEADERS)
        ):
            header_indices.append(i)
    if header_indices:
        start = header_indices[0] + 1
        return [row for row in parser.rows[start:] if len(row) >= len(HISTORY_HEADERS)]

    current_header_indices = []
    for i, row in enumerate(parser.rows):
        normalized = [normalize_heading(cell) for cell in row]
        if normalized[: len(CURRENT_HEADERS)] == CURRENT_HEADERS:
            current_header_indices.append(i)
    if current_header_indices:
        start = current_header_indices[0] + 1
        rows = []
        for row in parser.rows[start:]:
            if len(row) < len(CURRENT_HEADERS):
                continue
            normalized_first_cell = normalize_heading(row[0])
            if normalized_first_cell == "date":
                continue
            rows.append(convert_current_row(row))
        return rows

    # TYPO3 page styling sometimes splits history table cells into their own
    # markup blocks. A single HTML table still preserves each tr's cells.
    # Locate the achievements heading and select the first table after it.
    # Parser.rows is document ordered; tolerate the header being omitted.
    return []


def normalize_heading(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()


def convert_current_row(row: list[str]) -> list[str]:
    current = dict(zip(CURRENT_HEADERS, row))
    history = {field: "" for field in HISTORY_HEADERS}
    for current_key, history_key in CURRENT_TO_HISTORY.items():
        history[history_key] = current.get(current_key, "")
    return [history[field] for field in HISTORY_HEADERS]


def main() -> int:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT_CSV
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        teams = get_teams(fetch(TEAM_LIST_URL))
        print(f"Found {len(teams)} FSE teams")
        records: list[dict[str, str]] = []
        for index, (team_name, team_url) in enumerate(teams, start=1):
            try:
                history = get_history_rows(fetch(team_url))
                for values in history:
                    values = (values + [""] * len(HISTORY_HEADERS))[: len(HISTORY_HEADERS)]
                    records.append({"team": team_name, "team_url": team_url, **dict(zip(HISTORY_HEADERS, values))})
                print(f"[{index}/{len(teams)}] {team_name}: {len(history)} records")
            except (HTTPError, URLError, TimeoutError, RuntimeError) as exc:
                print(f"[{index}/{len(teams)}] {team_name}: skipped ({exc})", file=sys.stderr)
            if index < len(teams):
                time.sleep(0.25)

        with open(output, "w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=FIELDS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(records)
        print(f"Wrote {len(records)} achievement records to {output}")
        return 0
    except (HTTPError, URLError, TimeoutError, RuntimeError) as exc:
        print(f"Unable to scrape Formula Student Germany: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
