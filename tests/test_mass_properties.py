"""Excel provenance, inertia axes, and the three branches of the shared source."""

import csv
from html import unescape
import os
from pathlib import Path
import re
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import matplotlib
matplotlib.use("Agg")
import numpy as np
import pandas as pd
from PySide6.QtWidgets import QApplication, QFormLayout, QWidget

from analysis import COG_movable as cog
from analysis_data import load_analysis_parameters, parse_analysis_parameters
from main import MainWindow
from plugin_loader import scan_analysis

ROOT = Path(__file__).resolve().parents[1]


class MassPropertiesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = load_analysis_parameters(ROOT / "data/analysis_parameters.csv")
        cls.plugins = {p.plugin_id: p for p in scan_analysis()}
        cls.parameters = parse_analysis_parameters(cls.inputs, cog.PARAMETERS)
        cls.components, cls.summary, cls.outputs = cog.calculate(cls.parameters)
        with (ROOT / "data/analysis_flow.csv").open(encoding="utf-8-sig", newline="") as stream:
            cls.flow = list(csv.DictReader(stream))

    def test_excel_mass_and_inertia_controls(self):
        expected = {"ms": 260.55, "mu": 14.4, "mu_front": 14.5, "mu_rear": 14.3,
                    "cog_total_mass_kg": 318.15, "cog_unsprung_front_mass_kg": 29,
                    "cog_unsprung_rear_mass_kg": 28.6, "L": 1.53,
                    "hl_sprung_roll_inertia_kg_m2": 7.917820044730288}
        self.assertEqual(set(self.outputs), set(cog.OUTPUTS))
        for name, value in expected.items():
            self.assertAlmostEqual(self.outputs[name], value, places=10, msg=name)
        self.assertEqual(len(self.components), 39)
        self.assertTrue(all(Path(p).is_file() for p in self.components.source_file))
        self.assertNotIn("h_cog", self.outputs)
        self.assertAlmostEqual(self.outputs["ms"] + 4*self.outputs["mu"], self.outputs["cog_total_mass_kg"])

    def test_axle_moments_and_sprung_static_loads_conserve_mass(self):
        o = self.outputs
        expected_front = sum(self.components.mass_kg *
                             (self.components.x_m-o["cog_rear_axle_x_used_m"]) / o["L"])
        self.assertAlmostEqual(o["hl_front_weight_ratio"] * o["cog_total_mass_kg"], expected_front)
        self.assertAlmostEqual(o["ms"] * o["hl_sprung_front_weight_ratio"] + 2*o["mu_front"], expected_front)

    def test_unsprung_lateral_coordinates_follow_source_dimensionless_units(self):
        front = self.components[self.components.name == "FL_wheel_end"].iloc[0]
        rear = self.components[self.components.name == "RL_wheel_end"].iloc[0]
        self.assertAlmostEqual(front.y_m, .61926*self.parameters["t"])
        self.assertAlmostEqual(rear.y_m, .6185*self.parameters["hl_rear_track_m"])

    def test_parallel_axis_theorem_and_translation_invariance(self):
        frame = pd.DataFrame(dict(mass_kg=[2., 3., 4.], x_m=[1., -2., .5],
                                  y_m=[-.3, .2, .6], z_m=[.1, .7, -.2]))
        prop = cog.mass_properties(frame)
        center = prop["cg_m"]
        shift = prop["mass_kg"] * (np.eye(3)*np.dot(center, center)-np.outer(center, center))
        np.testing.assert_allclose(prop["inertia_datum_kg_m2"], prop["inertia_cg_kg_m2"]+shift)
        translated = frame.copy()
        translated[["x_m", "y_m", "z_m"]] += np.array([4., -3., 7.])
        np.testing.assert_allclose(cog.mass_properties(translated)["inertia_cg_kg_m2"], prop["inertia_cg_kg_m2"])
        self.assertTrue(np.all(np.linalg.eigvalsh(prop["inertia_cg_kg_m2"]) > 0))

    def test_moving_driver_updates_front_weight_ratio(self):
        original = cog.read_mass_file

        def moved(*args, **kwargs):
            frame = original(*args, **kwargs)
            frame.loc[frame.name == "Driver", "x_m"] += .1
            return frame

        with patch.object(cog, "read_mass_file", side_effect=moved):
            _, _, outputs = cog.calculate(self.parameters)
        self.assertAlmostEqual(outputs["hl_front_weight_ratio"]-self.outputs["hl_front_weight_ratio"],
                               86*.1/(318.15*1.53))

    def test_root_has_exactly_the_requested_three_outgoing_edges(self):
        captures = []
        MainWindow.build_flow_buttons(SimpleNamespace(flow=self.flow, flow_view=SimpleNamespace(setHtml=captures.append)))
        source = unescape(re.search(r'<div class="mermaid">(.*?)</div>', captures[0], re.S).group(1))
        ids = {r["node_id"]: f"flow_node_{i}" for i, r in enumerate(self.flow)}
        children = set(re.findall(rf'{ids["cog_movable"]} --> (flow_node_\d+)', source))
        self.assertEqual(children, {ids[n] for n in ("cg", "compressed_travel", "FWL")})

    def test_cached_values_never_skip_the_excel_source_or_stiffness_rebuild(self):
        cached = self.inputs | {name: str(value) for name, value in self.outputs.items()}
        cached |= {"Ks_pitch_N_per_m": "1", "Ks_roll_N_per_m": "1"}
        window = SimpleNamespace(flow=self.flow, plugins_by_id=self.plugins, parameter_values=cached)
        rows = MainWindow._required_analysis_rows(window, "hl_roll")
        ids = [r["node_id"] for r in rows]
        self.assertEqual(ids, ["cog_movable", "compressed_travel", "aero_stiffness", "frequency_stiffness",
                               "tire_stiffness", "overall_rigidity", "roll_center",
                               "roll_center_min_load_f", "roll_center_same_load_r", "hl_roll"])
        for selected in ("cg", "FWL"):
            self.assertEqual([r["node_id"] for r in MainWindow._required_analysis_rows(window, selected)],
                             ["cog_movable", selected])

    def test_derived_parameters_are_read_only_in_the_interface(self):
        app = QApplication.instance() or QApplication([])
        host = QWidget()
        window = SimpleNamespace(parameter_form=QFormLayout(host), parameter_edits={},
                                 parameter_values=self.inputs | {n: str(v) for n, v in self.outputs.items()} |
                                                 {"hl_front_roll_center_m": "0.021", "hl_rear_roll_center_m": "0.039"},
                                 output_names=set(cog.OUTPUTS) | {"hl_front_roll_center_m", "hl_rear_roll_center_m"},
                                 update_parameter=lambda *_: None)
        MainWindow.build_parameter_fields(window, self.plugins["hl_roll"])
        for name in ("ms", "mu", "mu_front", "mu_rear"):
            self.assertNotIn(name, window.parameter_edits)
        self.assertNotIn("hl_front_weight_ratio", window.parameter_edits)
        self.assertNotIn("hl_sprung_roll_inertia_kg_m2", window.parameter_edits)
        self.assertFalse(window.parameter_edits["h_cog"].isReadOnly())
        self.assertTrue(window.parameter_edits["hl_front_roll_center_m"].isReadOnly())
        self.assertTrue(window.parameter_edits["hl_rear_roll_center_m"].isReadOnly())
        MainWindow.build_parameter_fields(window, self.plugins["cog_movable"])
        self.assertFalse(cog.HIDDEN_PARAMETERS.intersection(window.parameter_edits))
        self.assertFalse({"cog_sprung_file", "cog_unsprung_front_file", "cog_unsprung_rear_file"}
                         .intersection(cog.PARAMETERS))
        self.assertFalse(window.parameter_edits["h_cog"].isReadOnly())
        # Check every node, including quarter-car panels, for removed mass fields.
        for plugin in self.plugins.values():
            MainWindow.build_parameter_fields(window, plugin)
            self.assertFalse({"ms", "mu", "mu_front", "mu_rear", "L", "hl_front_weight_ratio",
                              "hl_sprung_roll_inertia_kg_m2"}
                             .intersection(window.parameter_edits), plugin.plugin_id)
        host.close()

    def test_manual_height_is_preserved_when_excel_centroid_changes(self):
        original = cog.read_mass_file

        def moved(*args, **kwargs):
            frame = original(*args, **kwargs)
            frame["z_m"] += .15
            return frame

        values = self.parameters | {"h_cog": .42}
        with patch.object(cog, "read_mass_file", side_effect=moved):
            _, _, outputs = cog.calculate(values)
        self.assertAlmostEqual(outputs["cog_total_z_m"], self.outputs["cog_total_z_m"] + .15)
        self.assertEqual((values | outputs)["h_cog"], .42)
        self.assertNotIn("h_cog", outputs)

    def test_bad_sources_and_geometry_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "找不到"):
            cog.read_mass_file("data/input_data/not_present.xlsx", "sprung")
        for values in ({"h_cog": float("nan")}, {"cog_front_axle_x_m": "-100"},
                       {"cog_rear_axle_x_m": "2"}, {"t": 0}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                cog.calculate(self.parameters | values)


if __name__ == "__main__":
    unittest.main()
