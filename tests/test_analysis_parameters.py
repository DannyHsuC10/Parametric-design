"""Mass inputs have one name and one shared value across all analysis panels."""

import csv
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QFormLayout, QWidget

from analysis_data import (
    PARAMETER_ALIASES,
    load_analysis_parameters,
    normalize_analysis_parameters,
    parse_analysis_parameters,
)
from main import MainWindow
from plugin_loader import AnalysisPlugin, scan_analysis

ROOT = Path(__file__).resolve().parents[1]


class SharedParameterTests(unittest.TestCase):
    def test_old_csv_mass_names_load_as_ms_and_mu(self):
        with TemporaryDirectory(dir=ROOT) as temporary:
            folder = Path(temporary).resolve()
            self.assertTrue(folder.is_relative_to(ROOT.resolve()))
            path = folder / "legacy.csv"
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerows([
                    ["name", "number"], ["simulation_ms_total_kg", "300"],
                    ["simulation_mu_kg", "18"], ["simulation_corner_mass_kg", "75"],
                ])
            self.assertEqual(load_analysis_parameters(path), {
                "ms": "300", "mu": "18", "simulation_corner_mass_kg": "75",
            })

    def test_canonical_values_take_priority_independent_of_input_order(self):
        for entries in (
            {"ms": "260", "mu": "15", "simulation_ms_total_kg": "300", "simulation_mu_kg": "18"},
            {"simulation_ms_total_kg": "300", "simulation_mu_kg": "18", "ms": "260", "mu": "15"},
        ):
            self.assertEqual(normalize_analysis_parameters(entries), {"ms": "260", "mu": "15"})
            self.assertEqual(parse_analysis_parameters(entries, {"ms": "float", "mu": "float"}),
                             {"ms": 260.0, "mu": 15.0})

    def test_direct_plugin_calls_also_accept_legacy_inputs(self):
        module = SimpleNamespace(main=lambda parameters: parameters)
        plugin = AnalysisPlugin("legacy", module)
        self.assertEqual(plugin.run({"simulation_ms_total_kg": 300, "simulation_mu_kg": 18}),
                         {"ms": 300, "mu": 18})

    def test_all_plugin_parameters_use_canonical_mass_names(self):
        aliases = set(PARAMETER_ALIASES)
        plugins = scan_analysis()
        self.assertTrue(plugins)
        for plugin in plugins:
            self.assertFalse(aliases.intersection(plugin.parameters), plugin.plugin_id)
        for filename in ("analysis_parameters.csv", "analysis_parameters_last_set.csv"):
            with (ROOT / "data" / filename).open(encoding="utf-8-sig", newline="") as stream:
                names = [row["name"] for row in csv.DictReader(stream)]
            self.assertEqual(names.count("ms"), 1)
            self.assertEqual(names.count("mu"), 1)
            self.assertFalse(aliases.intersection(names))

    def test_editing_one_panel_updates_other_panels_and_invalidates_outputs(self):
        app = QApplication.instance() or QApplication([])
        host = QWidget()
        form = QFormLayout(host)
        window = SimpleNamespace(
            parameter_form=form, parameter_edits={},
            parameter_values={"ms": "260", "mu": "15", "Ks": "60000"},
            output_names={"Ks"}, output_values={"Ks": 60000},
        )
        window.update_parameter = lambda name, value: MainWindow.update_parameter(window, name, value)
        plugins = {plugin.plugin_id: plugin for plugin in scan_analysis()}
        MainWindow.build_parameter_fields(window, plugins["ode_spring"])
        self.assertEqual(set(window.parameter_edits), {"ms", "mu"})
        window.parameter_edits["ms"].setText("300")
        window.parameter_edits["mu"].setText("18")
        self.assertEqual(window.parameter_values["ms"], "300")
        self.assertEqual(window.parameter_values["mu"], "18")
        self.assertNotIn("Ks", window.parameter_values)
        self.assertEqual(window.output_values, {})
        for stage in ("skidpad_test", "damped_oscillation_analysis", "hl_heave"):
            MainWindow.build_parameter_fields(window, plugins[stage])
            self.assertEqual(window.parameter_edits["ms"].text(), "300")
            self.assertEqual(window.parameter_edits["mu"].text(), "18")
        MainWindow.update_parameter(window, "simulation_ms_total_kg", "320")
        self.assertEqual(window.parameter_values["ms"], "320")
        self.assertNotIn("simulation_ms_total_kg", window.parameter_values)
        host.close()


if __name__ == "__main__":
    unittest.main()
