"""Check simulation flow dependencies and oscillator physics."""

import csv
from contextlib import redirect_stdout
import html
from io import StringIO
from pathlib import Path
import re
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg import expm

from app.analysis_data import load_analysis_parameters, parse_analysis_parameters
from main import MainWindow
from analysis.suspension_dynamics.oscillation_models import (
    analytical_response,
    explicit_euler,
    oscillator_energy,
    time_grid,
)
from app.plugin_loader import scan_analysis


ROOT = Path(__file__).resolve().parents[1]
NEW_IDS = ("analytical_numerical_simulation", "time_sensitivity", "ode_spring")


class SimulationFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        plt.switch_backend("Agg")
        cls.values = load_analysis_parameters(ROOT / "data" / "analysis_parameters.csv")
        with (ROOT / "data" / "analysis_flow.csv").open(encoding="utf-8-sig", newline="") as file:
            cls.flow = list(csv.DictReader(file))
        cls.plugins = {plugin.plugin_id: plugin for plugin in scan_analysis()}
        from analysis.COG_movable import calculate
        _, _, mass_outputs = calculate(parse_analysis_parameters(cls.values, cls.plugins["cog_movable"].parameters))
        cls.values.update({name: str(value) for name, value in mass_outputs.items()})

    def run_plugin(self, plugin_id, values):
        plugin = self.plugins[plugin_id]
        parameters = parse_analysis_parameters(values, plugin.parameters)
        with redirect_stdout(StringIO()):
            return plugin.run(parameters)

    def test_time_sensitivity_branches_from_tire_stiffness(self):
        rows = [row for row in self.flow if row["node_id"] in NEW_IDS]
        self.assertEqual([row["node_id"] for row in rows], [NEW_IDS[1], NEW_IDS[0], NEW_IDS[2]])
        self.assertEqual(rows[0]["flow_row"], "branch")
        self.assertEqual(rows[0]["branch_from"], "tire_stiffness")
        self.assertTrue(all(row["flow_row"] == "branch" for row in rows[1:]))
        self.assertEqual(rows[1]["branch_from"], "time_sensitivity")
        self.assertEqual(rows[2]["branch_from"], "analytical_numerical_simulation")
        captures = []
        window = SimpleNamespace(flow=self.flow, flow_view=SimpleNamespace(setHtml=captures.append))
        MainWindow.build_flow_buttons(window)
        source = html.unescape(re.search(r'<div class="mermaid">(.*?)</div>', captures[0], re.S).group(1))
        graph_ids = {row["node_id"]: f"flow_node_{index}" for index, row in enumerate(self.flow)}
        new_graph_ids = {graph_ids[node] for node in NEW_IDS}
        edges = set(re.findall(r"(flow_node_\d+) --> (flow_node_\d+)", source))
        related = {(first, second) for first, second in edges if first in new_graph_ids or second in new_graph_ids}
        self.assertEqual(related, {
            (graph_ids["tire_stiffness"], graph_ids[NEW_IDS[1]]),
            (graph_ids[NEW_IDS[1]], graph_ids["critical_damping_analysis"]),
            (graph_ids[NEW_IDS[1]], graph_ids[NEW_IDS[0]]),
            (graph_ids[NEW_IDS[0]], graph_ids[NEW_IDS[2]]),
            (graph_ids[NEW_IDS[2]], graph_ids["damping_ode"]),
        })

    def test_all_flow_parameters_resolve_in_execution_order(self):
        values = {name: str(value) for plugin in self.plugins.values()
                  for name, value in plugin.parameter_defaults.items()} | self.values
        available = set(values)
        context = SimpleNamespace(flow=self.flow, plugins_by_id=self.plugins, parameter_values=values)
        for row in MainWindow._all_analysis_rows_in_dependency_order(context):
            plugin = self.plugins[row["analysis_id"]]
            self.assertFalse(set(plugin.parameters) - available, row["node_id"])
            available.update(plugin.outputs)

    def test_new_plugins_do_not_create_figures_during_import(self):
        before = set(plt.get_fignums())
        plugins = {plugin.plugin_id: plugin for plugin in scan_analysis()}
        self.assertTrue(set(NEW_IDS).issubset(plugins))
        self.assertEqual(set(plt.get_fignums()), before)

    def test_selected_simulations_resolve_their_mass_and_stiffness_sources(self):
        window = SimpleNamespace(flow=self.flow, plugins_by_id=self.plugins,
                                 parameter_values=dict(self.values))
        for selected in NEW_IDS:
            required = MainWindow._required_analysis_rows(window, selected)
            required_ids = {row["node_id"] for row in required}
            self.assertEqual(required_ids, {
                "cog_movable", "compressed_travel", "aero_stiffness", "frequency_stiffness",
                "tire_stiffness", selected,
            })

    def test_shared_quarter_mass_and_result_plots(self):
        values = dict(self.values, ms="260", mu="15", Ks="60000")
        expected_axes = (3, 4, 3)
        for plugin_id, axis_count in zip(NEW_IDS, expected_axes):
            with patch.object(self.plugins[plugin_id].module, "SIMULATION_TIME_S", 0.2):
                result = self.run_plugin(plugin_id, values)
                figure, outputs = result
            try:
                self.assertEqual(len(figure.axes), axis_count)
                self.assertTrue(all(np.isfinite(value) for value in outputs.values()))
                self.assertEqual(set(outputs), set(self.plugins[plugin_id].outputs))
                plugin = self.plugins[plugin_id]
                self.assertEqual(set(plugin.parameters) - plugin.hidden_parameters,
                                 {"ms", "mu"}
                                 if plugin_id == "ode_spring" else {"ms"})
                values.update({name: str(value) for name, value in outputs.items()})
            finally:
                if hasattr(result, "close"):
                    result.close()
                else:
                    plt.close(figure)
        self.assertEqual(float(values["simulation_corner_mass_kg"]), 65)
        self.assertEqual(float(values["simulation_sensitivity_mass_used_kg"]), 65)
        self.assertEqual(float(values["simulation_sensitivity_stiffness_used_N_per_m"]), 60000)

    def test_euler_energy_growth_matches_theoretical_factor(self):
        times = time_grid(1.0, 0.01)
        displacement, velocity = explicit_euler(2, 8, 0.05, 0.02, times)
        energy = oscillator_energy(2, 8, displacement, velocity)
        expected = (1 + (8 / 2) * 0.01**2) ** np.arange(len(times))
        np.testing.assert_allclose(energy / energy[0], expected, rtol=1e-12)
        exact_x, exact_v = analytical_response(2, 8, 0.05, 0.02, times)
        exact_energy = oscillator_energy(2, 8, exact_x, exact_v)
        np.testing.assert_allclose(exact_energy, exact_energy[0], rtol=1e-13)

    def test_rk45_matches_exact_linear_quarter_car_response(self):
        module = self.plugins["ode_spring"].module
        with patch.multiple(module, SIMULATION_TIME_S=0.25, OUTPUT_TIME_STEP_S=0.01,
                            RK45_RTOL=1e-9, RK45_ATOL=1e-12):
            figure, outputs = self.run_plugin("ode_spring", dict(self.values, ms="260", mu="15", Ks="60000"))
        try:
            ms, mu, ks, kt = 65, 15, 60000, 100000
            matrix = np.array([[0, 1, 0, 0], [-ks/ms, 0, ks/ms, 0],
                               [0, 0, 0, 1], [ks/mu, 0, -(ks+kt)/mu, 0]])
            expected = expm(matrix * 0.25) @ np.array([0, 0, 0.025, 0])
            self.assertAlmostEqual(figure.axes[0].lines[0].get_ydata()[-1], expected[0], delta=1e-9)
            self.assertAlmostEqual(figure.axes[0].lines[1].get_ydata()[-1], expected[2], delta=1e-9)
            self.assertLess(outputs["simulation_rk45_max_energy_error_percent"], 1e-5)
        finally:
            plt.close(figure)

    def test_zero_initial_state_has_zero_energy_error(self):
        with patch.multiple(self.plugins["ode_spring"].module, SIMULATION_TIME_S=0.1,
                            INITIAL_STATE=(0.0, 0.0, 0.0, 0.0)):
            figure, outputs = self.run_plugin("ode_spring", dict(self.values, Ks="60000"))
        try:
            self.assertEqual(outputs["simulation_rk45_initial_energy_J"], 0)
            self.assertEqual(outputs["simulation_rk45_max_energy_error_percent"], 0)
        finally:
            plt.close(figure)

    def test_time_grid_covers_exact_interval(self):
        for duration, step in ((1, 0.3), (1, 2), (1e-14, 0.001), (5, 0.001)):
            with self.subTest(duration=duration, step=step):
                times = time_grid(duration, step)
                self.assertEqual(times[0], 0)
                self.assertEqual(times[-1], duration)
                self.assertTrue(np.all(np.diff(times) > 0))
                self.assertTrue(np.all(times <= duration))


if __name__ == "__main__":
    unittest.main()
