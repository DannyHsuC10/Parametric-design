"""Motor curves feed maximum torque into the graph and incremental gearing runs."""

from contextlib import ExitStack, redirect_stdout
import csv
import importlib
from io import StringIO
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PySide6.QtWidgets import QApplication, QFormLayout, QWidget

from analysis import motor
from analysis.gearing.workflow import DEFAULTS
from analysis_data import parse_analysis_parameters
from analysis_runner import AnalysisRunner
from flow_diagram import flow_edges
from main import MainWindow
from plugin_loader import scan_analysis

ROOT = Path(__file__).resolve().parents[1]


class MotorTests(unittest.TestCase):
    def test_curve_and_maximum_torque_match_the_supplied_csv(self):
        supplied = pd.read_csv(ROOT / "data" / "input_data" / "motor_speed_vs_torque.csv")
        result = motor.main({})
        try:
            pd.testing.assert_frame_equal(result.tables["motor_speed_vs_torque.csv"], supplied)
            self.assertEqual(result.outputs["drive_motor_torque_Nm"], supplied["torque"].max())
            self.assertAlmostEqual(result.outputs["drive_motor_torque_Nm"], 22.30565254)
            self.assertEqual(result.outputs["motor_peak_torque_rpm"], 0.0)
            self.assertEqual(result.outputs["motor_curve_max_rpm"], 22000.0)
            self.assertEqual(result.outputs["motor_sample_count"], 500)
            line = result.figure.axes[0].lines[0]
            np.testing.assert_array_equal(line.get_xdata(), supplied["speed"])
            np.testing.assert_array_equal(line.get_ydata(), supplied["torque"])
            self.assertIn("max(torque)", result.artifacts["analysis.md"])
        finally:
            result.close()

    def test_import_does_not_read_data_plot_or_write_files(self):
        with patch("pandas.read_csv") as read, patch.object(plt, "subplots") as plot:
            importlib.reload(motor)
        read.assert_not_called()
        plot.assert_not_called()

    def test_graph_includes_independent_motor_source_and_downstream_dependencies(self):
        plugins = {p.plugin_id: p for p in scan_analysis()}
        with (ROOT / "data" / "analysis_flow.csv").open(encoding="utf-8-sig", newline="") as stream:
            flow = list(csv.DictReader(stream))
        edges = flow_edges(flow)
        self.assertIn(("motor", "gear_rate"), edges)
        self.assertIn(("acc_load", "gear_rate"), edges)
        self.assertFalse(any(target == "motor" for source, target in edges))
        self.assertEqual(next(row["flow_group"] for row in flow if row["node_id"] == "motor"), "傳動分析")
        window = SimpleNamespace(flow=flow, plugins_by_id=plugins,
                                 parameter_values={key: "1" for p in plugins.values() for key in p.parameters})
        for node in ("gear_rate", "output_check", "acc_resis", "tooth_strength"):
            rows = MainWindow._required_analysis_rows(window, node)
            ids = [row["node_id"] for row in rows]
            self.assertLess(ids.index("motor"), ids.index(node))
        torque_producers = [p.plugin_id for p in plugins.values() if "drive_motor_torque_Nm" in p.outputs]
        self.assertEqual(torque_producers, ["motor"])

    def test_downstream_maximum_torque_field_is_read_only(self):
        app = QApplication.instance() or QApplication([])
        plugins = {p.plugin_id: p for p in scan_analysis()}
        host = QWidget()
        window = SimpleNamespace(parameter_form=QFormLayout(host), parameter_edits={},
                                 parameter_values={"drive_motor_torque_Nm": "22.30565254"},
                                 output_names={name for p in plugins.values() for name in p.outputs},
                                 update_parameter=Mock())
        try:
            for node in ("gear_rate", "output_check", "acc_resis", "tooth_strength"):
                MainWindow.build_parameter_fields(window, plugins[node])
                edit = window.parameter_edits["drive_motor_torque_Nm"]
                self.assertTrue(edit.isReadOnly())
                self.assertEqual(edit.text(), "22.30565254")
                self.assertIn("max(torque)", edit.toolTip())
        finally:
            host.close()

    def test_invalid_source_data_is_rejected(self):
        invalid = (
            "speed,force\n0,10\n100,20\n", "speed,torque\n0,ten\n100,20\n",
            "speed,torque\n0,10\n100,nan\n", "speed,torque\n0,10\n",
            "speed,torque\n0,10\n0,20\n", "speed,torque\n-100,10\n0,20\n",
            "speed,torque\n0,0\n100,-1\n",
        )
        with TemporaryDirectory(dir=ROOT) as temporary:
            path = Path(temporary) / "motor.csv"
            for content in invalid:
                with self.subTest(content=content):
                    path.write_text(content, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        motor.load_curve(path)

    def test_curve_changes_recompute_motor_then_gear_rate_and_save_real_results(self):
        plugins = {p.plugin_id: p for p in scan_analysis()}
        rows = [dict(node_id=node, analysis_id=node, title=node) for node in ("motor", "gear_rate")]
        values = DEFAULTS | {"cog_total_mass_kg": 300, "L": 1.53, "h_cog": 0.3,
                             "hl_front_weight_ratio": 0.5, "R_tire": 0.2}
        values = {key: str(value) for key, value in values.items()}
        with TemporaryDirectory(dir=ROOT) as temporary, ExitStack() as stack:
            folder = Path(temporary)
            curve = folder / "motor.csv"
            curve.write_text("speed,torque\n0,20\n10000,10\n", encoding="utf-8")
            stack.enter_context(patch.object(motor, "CURVE_FILE", curve))
            plugins["motor"].input_files = (curve,)

            def run():
                runner = AnalysisRunner(plugins, rows, values, folder / "results", incremental=True)
                with redirect_stdout(StringIO()):
                    runner.run()
                self.assertIsNone(runner.error)
                return runner

            first = run()
            self.assertEqual((first.completed_count, first.reused_count), (2, 0))
            self.assertEqual(float(first.values["drive_motor_torque_Nm"]), 20)
            unchanged = run()
            self.assertEqual((unchanged.completed_count, unchanged.reused_count), (0, 2))
            curve.write_text("speed,torque\n0,40\n10000,10\n", encoding="utf-8")
            changed = run()
            self.assertEqual((changed.completed_count, changed.reused_count), (2, 0))
            self.assertEqual(float(changed.values["drive_motor_torque_Nm"]), 40)
            self.assertAlmostEqual(float(changed.values["gear_ratio_accel"]),
                                   float(first.values["gear_ratio_accel"]) / 2)
            for name in ("plot.png", "result.csv", "motor_speed_vs_torque.csv", "cache.json", "analysis.md"):
                self.assertTrue((folder / "results" / "motor" / name).is_file())
            with (folder / "results" / "gear_rate" / "result.csv").open(encoding="utf-8-sig", newline="") as stream:
                parameters = {row["name"]: row["number"] for row in csv.DictReader(stream)
                              if row["category"] == "輸入量"}
            parsed = parse_analysis_parameters(parameters, plugins["gear_rate"].parameters)
            self.assertEqual(parsed["drive_motor_torque_Nm"], 40)


if __name__ == "__main__":
    unittest.main()
