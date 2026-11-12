"""Verify the local crawler's CSV matching and publication behavior."""

import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import refresh_formula_student_data as crawler


TEAM_ONE = crawler.TEAM_URL.format("101")
TEAM_TWO = crawler.TEAM_URL.format("202")
TEAM_LIST = f"""
<a href="{TEAM_ONE}">Team One</a>
<a href="{TEAM_ONE}/">Team One</a>
<a href="{TEAM_TWO}">Team One</a>
"""
YEARS = range(2020, 2025)
CAR_CARDS = "".join(
    f"""
<div class="timeline-card " data-year="{year}">
  <div class="timeline-card-header"><span class="car-name-small">Car {year}</span></div>
  <h5>Car Specifications</h5>
  <table><tr><td>Wheelbase</td><td>1550 mm</td></tr></table>
</div>
"""
    for year in YEARS
)
RESULTS_TABLE = (
    "<table><tr><th>Date</th><th>Event</th><th>Teams</th><th>Rank</th>"
    "<th>SP</th><th>DV SP</th><th>AC</th><th>DV AC</th><th>AX</th></tr>"
    + "".join(
        f"<tr><td>{year}.08</td><td>FS DE</td><td>80</td><td>1.</td>"
        "<td>2.</td><td>7.</td><td>3.</td><td>8.</td><td>4.</td></tr>"
        for year in YEARS
    )
    + "</table>"
)
PAGES = {
    crawler.TEAM_LIST_URL: TEAM_LIST,
    TEAM_ONE: CAR_CARDS + "<h3>FS past achievements</h3>" + RESULTS_TABLE,
    TEAM_TWO: RESULTS_TABLE,
}
FILENAMES = (crawler.VEHICLE_CSV, crawler.RESULTS_CSV, crawler.MATCHED_CSV, crawler.METADATA_JSON)


class FormulaStudentRefreshTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.data_dir = Path(temporary.name)
        crawler.write_csv(self.data_dir / crawler.VEHICLE_CSV, crawler.VEHICLE_FIELDS, [
            {"team": "Retired Team", "team_id": "303", "year": "2019", "Wheelbase": "1600 mm"},
        ])
        crawler.write_csv(self.data_dir / crawler.RESULTS_CSV, crawler.RESULT_FIELDS, [])
        crawler.write_csv(self.data_dir / crawler.MATCHED_CSV, crawler.MATCHED_FIELDS, [])
        (self.data_dir / crawler.METADATA_JSON).write_text(
            '{"last_successful_crawl":"2020-01-01T00:00:00Z"}', encoding="utf-8",
        )

    def snapshot(self):
        return {name: (self.data_dir / name).read_bytes() for name in FILENAMES}

    def test_refresh_matches_ids_and_records_the_time(self):
        with patch.object(crawler, "fetch_html", side_effect=PAGES.__getitem__) as fetch:
            with patch.object(crawler, "REQUEST_INTERVAL", 0):
                crawler.refresh(self.data_dir)

        self.assertEqual([call.args[0] for call in fetch.call_args_list], list(PAGES))
        cars = crawler.read_existing_csv(self.data_dir / crawler.VEHICLE_CSV)
        self.assertEqual({car["team_id"] for car in cars}, {"101", "303"})
        results = crawler.read_existing_csv(self.data_dir / crawler.RESULTS_CSV)
        self.assertEqual(len(results), 10)
        self.assertEqual((results[0]["skidpad"], results[0]["acceleration"], results[0]["autocross"]), ("2.", "3.", "4."))
        matched = crawler.read_existing_csv(self.data_dir / crawler.MATCHED_CSV)
        self.assertEqual(len(matched), 5)
        self.assertEqual({row["team_url"] for row in matched}, {TEAM_ONE})
        self.assertEqual({row["vehicle_Wheelbase"] for row in matched}, {"1550 mm"})
        metadata = json.loads((self.data_dir / crawler.METADATA_JSON).read_text(encoding="utf-8"))
        stamp = datetime.fromisoformat(metadata["last_successful_crawl"].replace("Z", "+00:00"))
        self.assertEqual(stamp.tzinfo, timezone.utc)
        self.assertGreater(stamp.year, 2020)

    def test_crawl_failure_preserves_all_files(self):
        before = self.snapshot()
        with patch.object(crawler, "fetch_html", side_effect=[TEAM_LIST, PAGES[TEAM_ONE], RuntimeError("offline")]):
            with patch.object(crawler, "REQUEST_INTERVAL", 0):
                with self.assertRaisesRegex(RuntimeError, "offline"):
                    crawler.refresh(self.data_dir)
        self.assertEqual(self.snapshot(), before)
        self.assertFalse((self.data_dir / ".refresh.lock").exists())

    def test_failure_during_publication_restores_all_files(self):
        before = self.snapshot()
        replace = os.replace

        def replace_unless_locked(source, destination):
            if destination == self.data_dir / crawler.MATCHED_CSV:
                raise PermissionError("File is open in another program")
            replace(source, destination)

        with patch.object(crawler, "fetch_html", side_effect=PAGES.__getitem__):
            with patch.object(crawler, "REQUEST_INTERVAL", 0):
                with patch.object(crawler.os, "replace", side_effect=replace_unless_locked):
                    with self.assertRaises(PermissionError):
                        crawler.refresh(self.data_dir)
        self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
