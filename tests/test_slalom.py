"""Check the source geometry, shared track width, and Slalom workflow exports."""

from contextlib import redirect_stdout
import importlib
from io import StringIO
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis import Slalom
from analysis.cornering.models import slalom_geometry
from app.analysis_data import load_analysis_parameters, parse_analysis_parameters
from app.analysis_result import save_analysis_result
from new.Slalom import slalom_path_analysis
from app.plugin_loader import AnalysisPlugin

ROOT = Path(__file__).resolve().parents[1]


class SlalomTests(unittest.TestCase):
    def run_plugin(self, **overrides):
        values = load_analysis_parameters(ROOT / "data/analysis_parameters.csv") | overrides
        plugin = AnalysisPlugin("Slalom", Slalom)
        with redirect_stdout(StringIO()):
            return plugin.run(parse_analysis_parameters(values, plugin.parameters))

    def test_radii_match_the_original_with_the_same_front_track(self):
        with redirect_stdout(StringIO()):
            expected = slalom_path_analysis(show_plot=False)
        result = self.run_plugin(t="1.28")
        try:
            np.testing.assert_allclose(result.tables["slalom_geometry.csv"].curve_radius_m,
                                       expected, rtol=1e-14)
            self.assertEqual(len(result.figure.axes), 3)
        finally:
            result.close()

    def test_arc_circle_is_tangent_and_intersects_the_cone_midpoint(self):
        offsets, clearance, radii, angles = slalom_geometry(10, [0, 0.01, 1/6, 1/3],
                                                         1.25, 0.16, 0.2, 7)
        # At a cone, the path is exactly clearance away. At the midpoint
        # between adjacent alternating cones, the circular path crosses y=0.
        centers_y = offsets + clearance - radii
        np.testing.assert_allclose((3.5)**2 + centers_y**2, radii**2)
        np.testing.assert_allclose(centers_y + radii - offsets, clearance)
        self.assertTrue(np.isfinite(angles).all())
        with patch.multiple(Slalom, OFFSET_RATIOS=(0,), NUM_CONES=2):
            result = self.run_plugin()
        try:
            arcs = [patch for patch in result.figure.axes[0].patches
                    if isinstance(patch, matplotlib.patches.Arc)]
            self.assertAlmostEqual(arcs[0].center[1], -arcs[1].center[1])
            self.assertNotEqual(arcs[0].center[1], 0)
        finally:
            result.close()

    def test_shared_track_changes_results_and_multiple_figures_are_saved(self):
        with patch.object(Slalom, "OFFSET_RATIOS", (0, 0.01, 0.1, 0.2, 0.3)):
            result = self.run_plugin(t="1.4")
        try:
            self.assertEqual(set(result.outputs), set(Slalom.OUTPUTS))
            self.assertTrue(np.isfinite(list(result.outputs.values())).all())
            self.assertEqual(len(result.figure.axes), 4)
            self.assertEqual(len(result.figures["slalom_paths_2.png"].axes), 1)
            frame = result.tables["slalom_geometry.csv"]
            np.testing.assert_allclose(frame.front_track_m, 1.4)
            expected_clearance = 1.4/2 + 0.1905/2 + 0.16122034611053285 + 0.2
            np.testing.assert_allclose(frame.clearance_radius_m, expected_clearance)
            with TemporaryDirectory(dir=ROOT) as folder:
                save_analysis_result(folder, "slalom", {}, result)
                saved = Path(folder) / "slalom"
                plots = json.loads((saved / "plots.json").read_text(encoding="utf-8"))
                self.assertEqual(len(plots), 2)
                self.assertTrue(all((saved / item["file"]).is_file() for item in plots))
                pd.testing.assert_frame_equal(pd.read_csv(saved / "slalom_geometry.csv"), frame)
        finally:
            result.close()

    def test_import_has_no_plotting_printing_or_file_side_effects(self):
        figures = set(plt.get_fignums())
        with redirect_stdout(StringIO()) as output, patch.object(plt, "show") as show, \
                patch.object(plt, "savefig") as save:
            importlib.reload(Slalom)
        self.assertEqual(output.getvalue(), "")
        self.assertEqual(set(plt.get_fignums()), figures)
        show.assert_not_called()
        save.assert_not_called()

    def test_invalid_front_track_is_rejected_before_creating_figures(self):
        figures = set(plt.get_fignums())
        for overrides in ({"t": "0"}, {"t": "-1"}, {"t": "nan"}, {"t": "inf"}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                self.run_plugin(**overrides)
        self.assertEqual(set(plt.get_fignums()), figures)


if __name__ == "__main__":
    unittest.main()
