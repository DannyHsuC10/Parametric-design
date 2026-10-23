"""Recording analysis, interval weighting and flow integration."""

import csv
from pathlib import Path
import pickle
from tempfile import TemporaryDirectory
import unittest

import matplotlib
matplotlib.use("Agg")
import numpy as np

from analysis import Steady_lapsim
from analysis.steady_lapsim.workflow import INPUT_FILE, run
from app.analysis_result import save_analysis_result, load_plot_choices
from app.flow_diagram import flow_edges
from app.plugin_loader import scan_analysis


class SteadyLapsimTests(unittest.TestCase):
    def test_real_recording_and_exports(self):
        result = Steady_lapsim.main({})
        try:
            self.assertAlmostEqual(result.outputs["steady_lapsim_lap_time_s"], 93.06240693625188)
            self.assertEqual(result.outputs["steady_lapsim_sample_count"], 2487)
            phases = result.tables["phase_summary.csv"]
            self.assertAlmostEqual(phases.time_s.sum(), result.outputs["steady_lapsim_lap_time_s"])
            self.assertAlmostEqual(phases.distance_percent.sum(), 100)
            self.assertEqual(set(result.outputs), set(Steady_lapsim.OUTPUTS))
            with TemporaryDirectory() as folder:
                save_analysis_result(folder, "steady_lapsim", {}, result)
                target = Path(folder) / "steady_lapsim"
                self.assertEqual(len(load_plot_choices(target)), 2)
                self.assertTrue((target / "lap_samples.csv").exists())
                self.assertIn("93.062407", (target / "analysis.md").read_text(encoding="utf-8"))
        finally:
            result.close()

    def test_interval_weighting_and_validation(self):
        package = {"data": {"s_world": [[0, 0], [1, 0], [4, 0]],
                            "s": [0, 1, 4], "v": [1, 1, 1], "t": [0, 1, 4],
                            "phase": ["accelerate", "brake", "hold"]}}
        with TemporaryDirectory() as folder:
            path = Path(folder) / "test.pkl"
            path.write_bytes(pickle.dumps(package))
            result = run(path)
            try:
                np.testing.assert_allclose(result.tables["phase_summary.csv"].time_percent, [25, 75, 0])
            finally:
                result.close()
            for key, value in (("t", [0, 0, 4]), ("v", [-1, 1, 1]), ("s", [0, 3, 2]),
                               ("phase", ["bad", "hold", "hold"])):
                original = package["data"][key]
                package["data"][key] = value
                path.write_bytes(pickle.dumps(package))
                with self.assertRaises(ValueError):
                    run(path)
                package["data"][key] = original
            package["metadata"] = {"lap_time_s": 5}
            path.write_bytes(pickle.dumps(package))
            with self.assertRaisesRegex(ValueError, "lap_time_s"):
                run(path)

    def test_flow_has_exactly_three_incoming_edges_and_recording_is_tracked(self):
        with (INPUT_FILE.parents[1] / "analysis_flow.csv").open(encoding="utf-8-sig", newline="") as stream:
            flow = list(csv.DictReader(stream))
        self.assertEqual({a for a, b in flow_edges(flow) if b == "steady_lapsim"},
                         {"brake_force", "output_check", "aero_3d"})
        plugin = next(p for p in scan_analysis() if p.plugin_id == "steady_lapsim")
        self.assertEqual(plugin.input_files, (INPUT_FILE,))
        self.assertEqual(plugin.parameters, {})
