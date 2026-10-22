"""Brake-flow dependencies, hydraulic units and physical consistency."""

from contextlib import redirect_stdout
from html import unescape
from io import StringIO
import os
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis.braking.models import (G, LINE_DATA_PATH, axle_loads, fit_line_data,
                                     ideal_distribution)
from analysis.braking.workflow import DEFAULTS
from app.analysis_data import load_analysis_parameters, parse_analysis_parameters
from app.analysis_result import load_plot_choices, save_analysis_result
from main import MainWindow
from app.plugin_loader import scan_analysis

ROOT = Path(__file__).resolve().parents[1]
STAGES = ("brake_ratio", "pedal_ratio", "brake_force", "brake_hydraulic_pressure")
VEHICLE = {"cog_total_mass_kg": 300.0, "L": 1.5, "h_cog": 0.25,
           "hl_front_weight_ratio": 0.4, "mu_w": 1.0, "R_tire": 0.25}


class BrakingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plugins = {plugin.plugin_id: plugin for plugin in scan_analysis()}
        cls.flow = MainWindow.load_flow(SimpleNamespace(plugins_by_id=cls.plugins))

    def run_stage(self, stage, values):
        plugin = self.plugins[stage]
        with redirect_stdout(StringIO()):
            return plugin.run(parse_analysis_parameters(values, plugin.parameters))

    def test_requested_graph_and_selected_dependencies(self):
        captures = []
        window = SimpleNamespace(flow=self.flow, plugins_by_id=self.plugins,
                                 flow_view=SimpleNamespace(setHtml=captures.append),
                                 parameter_values=load_analysis_parameters(ROOT / "data/analysis_parameters.csv"))
        MainWindow.build_flow_buttons(window)
        source = unescape(re.search(r'<div class="mermaid">(.*?)</div>', captures[0], re.S).group(1))
        names = {f"flow_node_{i}": row["node_id"] for i, row in enumerate(self.flow)}
        edges = {(names[a], names[b]) for a, b in re.findall(r"(flow_node_\d+) --> (flow_node_\d+)", source)}
        self.assertEqual({edge for edge in edges if set(edge) & set(STAGES)}, {
            ("max_load", "brake_ratio"), ("brake_ratio", "pedal_ratio"),
            ("pedal_ratio", "brake_force"), ("pedal_ratio", "brake_hydraulic_pressure"),
        })
        self.assertIn(("max_load", "acc_load"), edges)
        self.assertFalse(any("pedal_box" in row["analysis_id"].lower() for row in self.flow))
        for stage in STAGES:
            rows = MainWindow._required_analysis_rows(window, stage)
            ids = [row["node_id"] for row in rows]
            self.assertIn("cog_movable", ids)
            self.assertIn("max_load", ids)
            self.assertEqual(ids[-1], stage)
            if stage == "brake_hydraulic_pressure":
                self.assertEqual(ids[-4:], ["max_load", "brake_ratio", "pedal_ratio", stage])
                self.assertNotIn("brake_force", ids)
            if stage == "brake_force":
                self.assertEqual(ids[-4:], ["max_load", "brake_ratio", "pedal_ratio", "brake_force"])

    def test_shared_defaults_and_imports_have_no_figures_or_csv_side_effects(self):
        before = set(plt.get_fignums())
        scan_analysis()
        self.assertEqual(set(plt.get_fignums()), before)
        for filename in ("analysis_parameters.csv", "analysis_parameters_last_set.csv"):
            values = load_analysis_parameters(ROOT / "data" / filename)
            for name, expected in DEFAULTS.items():
                self.assertIn(name, values)
                if filename == "analysis_parameters.csv":
                    self.assertAlmostEqual(float(values[name]), expected)
            if filename == "analysis_parameters.csv":
                self.assertNotIn("brake_pedal_ratio_required", values)
                self.assertNotIn("brake_pressure_target_MPa", values)

    def test_non_half_weight_distribution_and_force_balance(self):
        front, rear = axle_loads(VEHICLE, np.array([0, 1.0]))
        np.testing.assert_allclose(front, [1177.2, 1667.7])
        np.testing.assert_allclose(rear, [1765.8, 1275.3])
        front_force, rear_force = ideal_distribution(VEHICLE, np.array([0, 1.0]))
        np.testing.assert_allclose(front_force + rear_force, [0, 2943.0])
        result = self.run_stage("brake_ratio", DEFAULTS | VEHICLE)
        try:
            data = result.tables["ideal_brake_distribution.csv"]
            np.testing.assert_allclose(data.front_force_N + data.rear_force_N,
                                       VEHICLE["cog_total_mass_kg"] * G * data.deceleration_g)
        finally:
            result.close()

    def test_hand_calculated_caliper_force_has_no_factor_of_two_error(self):
        p = DEFAULTS | VEHICLE | {
            "cog_total_mass_kg": 200.0, "R_tire": 0.3, "brake_driver_force_N": 100.0,
            "brake_pedal_ratio_required": 2.0, "brake_balance_bar_front_ratio": 0.5,
            "brake_master_front_diameter_m": 0.02, "brake_master_rear_diameter_m": 0.02,
            "brake_caliper_front_piston_diameter_m": 0.03, "brake_caliper_rear_piston_diameter_m": 0.03,
            "brake_pad_mu": 0.5, "brake_disc_outer_diameter_m": 0.2, "brake_disc_contact_offset_m": 0.01,
        }
        result = self.run_stage("brake_force", p)
        try:
            self.assertAlmostEqual(result.outputs["brake_front_pressure_Pa"], 1e6 / np.pi)
            self.assertAlmostEqual(result.outputs["brake_front_force_N"], 270.0)
            self.assertAlmostEqual(result.outputs["brake_rear_force_N"], 270.0)
            self.assertAlmostEqual(result.outputs["brake_theoretical_deceleration_g"], 2.7 / G)
        finally:
            result.close()

    def test_pedal_sizing_satisfies_both_circuits_and_first_lock_matches_friction(self):
        p = DEFAULTS | VEHICLE | {"brake_safety_factor": 1.0}
        ratio = self.run_stage("brake_ratio", p)
        p.update(ratio.outputs)
        ratio.close()
        pedal = self.run_stage("pedal_ratio", p)
        p.update(pedal.outputs)
        pedal.close()
        result = self.run_stage("brake_force", p)
        try:
            out = result.outputs
            pressure_ratios = [out[f"brake_{axle}_pressure_Pa"] / p[f"brake_required_{axle}_pressure_Pa"]
                               for axle in ("front", "rear")]
            self.assertTrue(all(value >= 1 - 1e-12 for value in pressure_ratios))
            self.assertAlmostEqual(min(pressure_ratios), 1.0)
            force_fraction = out["brake_first_lock_driver_force_N"] / p["brake_driver_force_N"]
            demands = np.array([out["brake_front_force_N"], out["brake_rear_force_N"]]) * force_fraction
            loads = np.array(axle_loads(p, out["brake_first_lock_deceleration_g"]))
            utilization = demands / (p["mu_w"] * loads)
            self.assertAlmostEqual(utilization.max(), 1.0)
            self.assertTrue(np.all(utilization <= 1 + 1e-12))
            self.assertLessEqual(out["brake_deceleration_before_lock_g"], p["mu_w"] + 1e-12)
        finally:
            result.close()

    def test_pedal_line_pressures_include_safety_factor_and_match_brake_force(self):
        p = DEFAULTS | VEHICLE | {"brake_safety_factor": 1.5,
                                  "brake_balance_bar_front_ratio": 0.3,
                                  "brake_master_front_diameter_m": 0.02,
                                  "brake_master_rear_diameter_m": 0.025}
        ratio = self.run_stage("brake_ratio", p)
        p.update(ratio.outputs)
        ratio.close()
        pedal = self.run_stage("pedal_ratio", p)
        force = None
        try:
            p.update(pedal.outputs)
            force = self.run_stage("brake_force", p)
            table = pedal.tables["pedal_line_pressure.csv"].set_index("axle")
            applied_master_force = 0.0
            margins = []
            for axle in ("front", "rear"):
                pressure = pedal.outputs[f"brake_pedal_{axle}_pressure_Pa"]
                self.assertAlmostEqual(pressure, force.outputs[f"brake_{axle}_pressure_Pa"])
                self.assertAlmostEqual(pedal.outputs[f"brake_pedal_{axle}_pressure_MPa"], pressure / 1e6)
                self.assertAlmostEqual(table.loc[axle, "line_pressure_bar"], pressure / 1e5)
                self.assertAlmostEqual(table.loc[axle, "line_pressure_MPa"], pressure / 1e6)
                applied_master_force += pressure * np.pi * (p[f"brake_master_{axle}_diameter_m"] / 2) ** 2
                margins.append(pressure / p[f"brake_required_{axle}_pressure_Pa"])
            # Pressure * piston area recovers all of the amplified driver force.
            self.assertAlmostEqual(applied_master_force, p["brake_driver_force_N"] * p["brake_pedal_ratio_required"])
            self.assertAlmostEqual(min(margins), 1.5)
            self.assertAlmostEqual(pedal.outputs["brake_pedal_front_pressure_Pa"] /
                                   pedal.outputs["brake_pedal_rear_pressure_Pa"], (0.3 / 0.7) * (0.025 / 0.02) ** 2)
        finally:
            pedal.close()
            if force is not None:
                force.close()

    def test_rear_lift_and_low_friction_remain_in_contact(self):
        for changes in ({"mu_w": 0.02}, {"h_cog": 2.0}, {"h_cog": 0.0}):
            p = DEFAULTS | VEHICLE | changes
            result = self.run_stage("brake_ratio", p)
            try:
                data = result.tables["ideal_brake_distribution.csv"]
                self.assertTrue(np.all(data.rear_load_N >= 0))
                self.assertTrue(np.isfinite(data.to_numpy()).all())
                self.assertLessEqual(result.outputs["brake_design_deceleration_g"], p["mu_w"])
            finally:
                result.close()

    def test_moved_csv_fits_original_measurements_and_target_units(self):
        self.assertEqual(LINE_DATA_PATH, ROOT / "data/input_data/brake_line_data.csv")
        self.assertFalse((ROOT / "new/brake_line_data.csv").exists())
        fits = fit_line_data()
        for data, coefficients in fits.values():
            np.testing.assert_allclose(np.polyval(coefficients, data.pressure_MPa), data.expansion_mm3_per_m)
        pressures = {"brake_pedal_front_pressure_Pa": 10.3e6, "brake_pedal_rear_pressure_Pa": 6.9e6}
        result = self.run_stage("brake_hydraulic_pressure", pressures)
        try:
            self.assertAlmostEqual(result.outputs["brake_line_low_expansion_mm3_per_m"], 1380.0)
            self.assertAlmostEqual(result.outputs["brake_line_high_expansion_mm3_per_m"], 2590.0)
            self.assertTrue(result.outputs["brake_line_low_target_in_range"])
            self.assertAlmostEqual(result.outputs["brake_pressure_target_MPa"], 10.3)
            self.assertEqual(result.outputs["brake_pressure_source_axle"], "front")
        finally:
            result.close()
        extrapolated = self.run_stage("brake_hydraulic_pressure", pressures | {"brake_pedal_rear_pressure_Pa": 25e6})
        try:
            self.assertFalse(extrapolated.outputs["brake_line_high_target_in_range"])
            self.assertAlmostEqual(extrapolated.outputs["brake_pressure_target_MPa"], 25)
            self.assertEqual(extrapolated.outputs["brake_pressure_source_axle"], "rear")
        finally:
            extrapolated.close()

    def test_hydraulic_uses_pedal_outputs_and_ignores_old_manual_target(self):
        p = DEFAULTS | VEHICLE
        for stage in ("brake_ratio", "pedal_ratio"):
            result = self.run_stage(stage, p)
            p.update(result.outputs)
            result.close()
        # An old saved manual target must not override the upstream circuit pressures.
        with redirect_stdout(StringIO()):
            result = self.plugins["brake_hydraulic_pressure"].run(p | {"brake_pressure_target_MPa": 99.0})
        try:
            expected = max(p["brake_pedal_front_pressure_Pa"], p["brake_pedal_rear_pressure_Pa"]) / 1e6
            self.assertAlmostEqual(result.outputs["brake_pressure_target_MPa"], expected)
            frame = result.tables["brake_line_target.csv"]
            np.testing.assert_allclose(frame.target_pressure_MPa, expected)
            np.testing.assert_allclose(frame.front_line_pressure_MPa, p["brake_pedal_front_pressure_Pa"] / 1e6)
            np.testing.assert_allclose(frame.rear_line_pressure_MPa, p["brake_pedal_rear_pressure_Pa"] / 1e6)
        finally:
            result.close()
        tied = self.run_stage("brake_hydraulic_pressure", {
            "brake_pedal_front_pressure_Pa": 10.3e6, "brake_pedal_rear_pressure_Pa": 10.3e6})
        try:
            self.assertEqual(tied.outputs["brake_pressure_source_axle"], "front_and_rear")
            self.assertAlmostEqual(tied.outputs["brake_line_low_expansion_mm3_per_m"], 1380)
        finally:
            tied.close()

    def test_invalid_geometry_and_csv_are_rejected_before_plotting(self):
        p = DEFAULTS | VEHICLE | {"brake_ideal_front_ratio": 0.6}
        for changes in ({"brake_master_front_diameter_m": 0}, {"brake_balance_bar_front_ratio": 1},
                        {"brake_caliper_front_piston_count": 3}, {"brake_disc_contact_offset_m": 0.11},
                        {"brake_safety_factor": 0.5}, {"brake_driver_force_N": np.nan}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.run_stage("pedal_ratio", p | changes)
        for value in (-1, np.nan, np.inf):
            with self.subTest(pressure=value), self.assertRaises(ValueError):
                self.run_stage("brake_hydraulic_pressure", {
                    "brake_pedal_front_pressure_Pa": value, "brake_pedal_rear_pressure_Pa": 1e6})
        with TemporaryDirectory(dir=ROOT) as temporary:
            path = Path(temporary) / "invalid.csv"
            pd.DataFrame({"type": ["Low"] * 3, "pressure_MPa": [1, 1, 1],
                          "expansion_mm3_per_m": [10, 20, 30]}).to_csv(path, index=False)
            with self.assertRaises(ValueError):
                fit_line_data(path)

    def test_all_four_results_export_to_the_existing_gallery(self):
        values = DEFAULTS | VEHICLE
        with TemporaryDirectory(dir=ROOT) as temporary:
            destination = Path(temporary)
            for stage in STAGES:
                result = self.run_stage(stage, values)
                try:
                    self.assertEqual(set(result.outputs), set(self.plugins[stage].outputs))
                    self.assertTrue(result.tables)
                    self.assertTrue(all(len(figure.axes) <= 4 for figure in (result.figure, *result.figures.values())))
                    parameters = parse_analysis_parameters(values, self.plugins[stage].parameters)
                    save_analysis_result(destination, stage, parameters, result)
                    choices = load_plot_choices(destination / stage)
                    self.assertEqual(len(choices), 1 + len(result.figures))
                    self.assertTrue((destination / stage / "analysis.rendered.html").is_file())
                    values.update(result.outputs)
                finally:
                    result.close()


if __name__ == "__main__":
    unittest.main()
