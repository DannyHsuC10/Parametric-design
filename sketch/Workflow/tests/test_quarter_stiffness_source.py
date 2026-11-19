"""Quarter models consume the frequency target spring rate through the workflow."""

from contextlib import redirect_stdout
import csv
from io import StringIO
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

import matplotlib
matplotlib.use("Agg")
import numpy as np

from analysis.suspension_models.parameters import (
    QUARTER_STIFFNESS, STAGES, make_suspension, plugin_metadata,
)
from app.analysis_data import load_analysis_parameters, parse_analysis_parameters
from app.analysis_result import normalize_result
from app.plugin_loader import scan_analysis
from main import MainWindow

ROOT = Path(__file__).resolve().parents[1]
QUARTER_STAGES = [stage for stage, (family, _, _) in STAGES.items() if family == "quarter"]


class QuarterStiffnessSourceTests(unittest.TestCase):
    def test_declared_source_and_validation(self):
        for stage in QUARTER_STAGES:
            metadata = plugin_metadata(stage)
            self.assertIn(QUARTER_STIFFNESS, metadata["PARAMETERS"])
            self.assertIn(QUARTER_STIFFNESS, metadata["HIDDEN_PARAMETERS"])
            self.assertNotIn("Ks", metadata["PARAMETERS"])
        values = {"Ks": 35000., QUARTER_STIFFNESS: 47000., "MR": 0.8, "Kt": 95000.}
        suspension = make_suspension("quarter", values)
        self.assertEqual(suspension.ks, 47000.)
        self.assertAlmostEqual(suspension.kw, 47000 * 0.8**2)
        self.assertAlmostEqual(suspension.ride_rate,
                               suspension.kw * suspension.kt / (suspension.kw + suspension.kt))
        for value in (0, -1, np.nan, np.inf):
            with self.subTest(value=value), self.assertRaises(ValueError):
                make_suspension("quarter", {QUARTER_STIFFNESS: value})

    def test_all_four_models_use_frequency_mass_output_in_actual_case_configs(self):
        plugins = {plugin.plugin_id: plugin for plugin in scan_analysis()}
        values = {key: str(value) for plugin in plugins.values()
                  for key, value in plugin.parameter_defaults.items()}
        values.update(load_analysis_parameters(ROOT / "data/analysis_parameters.csv"))
        with (ROOT / "data/analysis_flow.csv").open(encoding="utf-8-sig", newline="") as stream:
            flow = list(csv.DictReader(stream))
        window = SimpleNamespace(flow=flow, plugins_by_id=plugins, parameter_values=values)
        with redirect_stdout(StringIO()):
            for stage in QUARTER_STAGES:
                rows = MainWindow._required_analysis_rows(window, stage)
                ids = [row["node_id"] for row in rows]
                self.assertLess(ids.index("frequency_mass"), ids.index(stage))
                for row in rows[:-1]:
                    plugin = plugins[row["analysis_id"]]
                    result = normalize_result(plugin.run(parse_analysis_parameters(values, plugin.parameters)))
                    try:
                        values.update({name: str(value) for name, value in result.outputs.items()})
                    finally:
                        result.close()
                plugin = plugins[stage]
                parameters = parse_analysis_parameters(values, plugin.parameters)
                result = plugin.run(parameters)
                try:
                    for config in json.loads(result.artifacts["cases.json"]):
                        self.assertEqual(config["suspension_parameters"]["ks"],
                                         float(values[QUARTER_STIFFNESS]))
                        self.assertNotIn("Ks", config["upstream_parameters"])
                finally:
                    result.close()

    def test_half_car_rates_keep_their_existing_sources(self):
        values = {"Ks": 35000., "Ks_pitch_N_per_m": 40000., "Ks_roll_N_per_m": 24000.,
                  QUARTER_STIFFNESS: 47000.}
        lr = make_suspension("LR", values)
        fr = make_suspension("FR", values)
        self.assertEqual((lr.k_heave, lr.k_roll), (20000., 12000.))
        self.assertEqual(fr.k_heave_f, 20000.)
