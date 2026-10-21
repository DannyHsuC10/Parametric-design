"""Track plugin integration, physical units, scoring, and exported results."""

from contextlib import redirect_stdout
import csv
import html
import importlib
from io import BytesIO, StringIO
import json
import os
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from analysis.track_analysis.geometry import build_track, radius_distributions, read_workbook
from analysis.track_analysis.score_weight import calculate_score_weights
from analysis.track_analysis.track_data import TrackData
from analysis_data import load_analysis_parameters, parse_analysis_parameters
from analysis_result import load_plot_choices, save_analysis_result
from main import MainWindow
from plugin_loader import scan_analysis

ROOT = Path(__file__).resolve().parents[1]


class TrackAnalysisTests(unittest.TestCase):
    def test_flow_preserves_track_connections_and_adds_turning_radius(self):
        plugins = {plugin.plugin_id: plugin for plugin in scan_analysis()}
        window = SimpleNamespace(plugins_by_id=plugins)
        with patch("main.QMessageBox.critical") as error:
            flow = MainWindow.load_flow(window)
        error.assert_not_called()
        self.assertEqual(len(flow), 44)
        window.flow = flow
        captures = []
        window.flow_view = SimpleNamespace(setHtml=captures.append)
        MainWindow.build_flow_buttons(window)
        source = html.unescape(re.search(r'<div class="mermaid">(.*?)</div>', captures[0], re.S).group(1))
        graph_ids = {row["node_id"]: f"flow_node_{index}" for index, row in enumerate(flow)}
        edges = set(re.findall(r"(flow_node_\d+) --> (flow_node_\d+)", source))
        outgoing = {target for start, target in edges if start == graph_ids["track_analysis"]}
        self.assertEqual(outgoing, {graph_ids[node] for node in
                                   ("skidpad_test", "compressed_travel", "psd", "turning_radius")})
        # Preserve the extra skidpad-to-suspension connection already in the workspace.
        self.assertIn((graph_ids["skidpad_test"], graph_ids["compressed_travel"]), edges)

    def test_imports_do_not_parse_arguments_read_track_json_or_create_figures(self):
        before = set(plt.get_fignums())
        with redirect_stdout(StringIO()) as output, patch("argparse.ArgumentParser.parse_args") as parse:
            for name in ("geometry", "track_data", "score_weight"):
                importlib.reload(importlib.import_module(f"analysis.track_analysis.{name}"))
            importlib.reload(importlib.import_module("analysis.TrackAnalysis"))
        self.assertEqual(output.getvalue(), "")
        parse.assert_not_called()
        self.assertEqual(set(plt.get_fignums()), before)

    def test_radius_time_uses_gravity_and_respects_the_speed_cap(self):
        track = {"r": np.array([0.1, -0.1, 0.0]), "dx": np.array([2.0, 3.0, 7.0])}
        lengths, times = radius_distributions(track, 100, 100, 1.7)
        self.assertAlmostEqual(sum(row["accumulated_length_m"] for row in lengths), 5.0)
        self.assertAlmostEqual(sum(row["accumulated_time_s"] for row in times),
                               5 / np.sqrt(1.7 * 9.81 * 10))
        _, capped = radius_distributions(track, 1, 100, 1.7)
        self.assertAlmostEqual(sum(row["accumulated_time_s"] for row in capped), 5.0)
        _, excluded = radius_distributions(track, 100, 5, 1.7)
        self.assertEqual(sum(row["accumulated_time_s"] for row in excluded), 0.0)

    def test_reconstructed_distances_cover_the_entire_workbook_track(self):
        _, segments, tables = read_workbook(ROOT / "data" / "input_data" / "input_map.xlsx")
        track = build_track(segments, tables, 0.1)
        self.assertAlmostEqual(track["dx"].sum(), track["x"][-1])
        self.assertTrue(np.all(track["dx"] > 0))
        self.assertLessEqual(float(track["dx"].max()), 0.1 + 1e-9)
        self.assertGreater(track["n"], 1000)
        for key in ("X", "Y", "Z", "r", "bank", "incl", "factor_grip", "sector"):
            self.assertEqual(len(track[key]), int(track["n"]))
        for step in (0, -1, np.nan, np.inf):
            with self.subTest(step=step), self.assertRaises(ValueError):
                build_track(segments, tables, step)

    def test_score_weight_conserves_the_event_score_pool(self):
        track = TrackData(Radius_distribution_time=[
            {"rank": 1, "radius_range_m": "9-10", "radius_center_m": 9.5, "accumulated_time_s": 1.0},
            {"rank": 2, "radius_range_m": "19-20", "radius_center_m": 19.5, "accumulated_time_s": 3.0},
        ])
        entries = calculate_score_weights(track)
        self.assertAlmostEqual(sum(item["total_score"] for item in entries), 425)
        self.assertEqual([item["rank"] for item in entries], [1, 2])
        by_radius = {item["radius_center_m"]: item for item in entries}
        self.assertEqual(by_radius[9.5]["skidpad_bonus"], 75)
        self.assertEqual(by_radius[9.5]["weighted_score"], 87.5)
        self.assertEqual(by_radius[19.5]["weighted_score"], 262.5)
        self.assertEqual(track.top_5_score_rate, 100)
        self.assertEqual(calculate_score_weights(TrackData()), [])
        with self.assertRaises(ValueError):
            calculate_score_weights(TrackData(Skidpad_score=-1))

    def test_gallery_and_original_npz_json_exports_work_with_the_shared_saver(self):
        plugin = next(plugin for plugin in scan_analysis() if plugin.plugin_id == "track_analysis")
        values = load_analysis_parameters(ROOT / "data" / "analysis_parameters.csv")
        parameters = parse_analysis_parameters(values, plugin.parameters)
        unrelated, _ = plt.subplots()
        with redirect_stdout(StringIO()):
            result = plugin.run(parameters)
        try:
            self.assertIn(unrelated.number, plt.get_fignums())
            self.assertEqual(set(result.outputs), set(plugin.outputs))
            self.assertTrue(all(np.isfinite(value) for value in result.outputs.values()))
            self.assertEqual(1 + len(result.figures), 11)
            self.assertTrue(all(len(figure.axes) <= 4 for figure in (result.figure, *result.figures.values())))
            with np.load(BytesIO(result.artifacts["OpenTRACK.npz"]), allow_pickle=False) as track:
                self.assertEqual(int(track["n"]), result.outputs["track_points"])
                self.assertAlmostEqual(track["dx"].sum(), result.outputs["track_length_m"])
            summary = json.loads(result.artifacts["track.json"])
            self.assertEqual(summary["total_score"], 425)
            self.assertAlmostEqual(sum(entry["total_score"] for entry in summary["Radius_distribution_score"]), 425)
            with TemporaryDirectory(dir=ROOT) as temporary:
                save_analysis_result(temporary, "track_analysis", parameters, result)
                folder = Path(temporary) / "track_analysis"
                self.assertEqual(len(load_plot_choices(folder)), 11)
                self.assertEqual((folder / "track.json").read_text(encoding="utf-8"), result.artifacts["track.json"])
                self.assertTrue((folder / "OpenTRACK.npz").is_file())
                self.assertIn("Map:", (folder / "OpenTRACK.log").read_text(encoding="utf-8"))
                with (folder / "radius_distribution_score.csv").open(encoding="utf-8-sig", newline="") as stream:
                    self.assertAlmostEqual(sum(float(row["total_score"]) for row in csv.DictReader(stream)), 425)
        finally:
            result.close()
            plt.close(unrelated)


if __name__ == "__main__":
    unittest.main()
