import unittest

from plugin_loader import scan_analysis
from analysis.gearing.workflow import DEFAULTS


class GearingIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plugins = {plugin.plugin_id: plugin for plugin in scan_analysis()}
        from analysis.motor import CURVE_FILE, load_curve
        cls.motor_outputs = {"drive_motor_torque_Nm": float(load_curve(CURVE_FILE)["torque"].max())}

    def test_requested_flow_edges_and_independent_branches_load(self):
        from pathlib import Path
        from types import SimpleNamespace
        from analysis_data import load_analysis_parameters
        from main import MainWindow

        window = SimpleNamespace(plugins_by_id=self.plugins)
        flow = MainWindow.load_flow(window, Path(__file__).resolve().parents[1] / "data" / "analysis_flow.csv")
        gearing_flow = [row for row in flow if row.get("flow_group") == "傳動分析"]
        self.assertEqual([row["node_id"] for row in gearing_flow], [
            "acc_load", "motor", "gear_rate", "gear_tooth", "number_of_gear", "output_check",
            "rotational_inertia", "acc_resis", "tooth_strength",
        ])
        self.assertEqual({row["node_id"]: row["branch_from"] for row in gearing_flow}, {
            "acc_load": "max_load", "motor": "", "gear_rate": "acc_load", "gear_tooth": "gear_rate",
            "number_of_gear": "gear_tooth", "output_check": "number_of_gear",
            "rotational_inertia": "number_of_gear", "acc_resis": "gear_rate",
            "tooth_strength": "gear_tooth",
        })
        window.flow = flow
        window.parameter_values = ({name: str(value) for plugin in self.plugins.values()
                                    for name, value in plugin.parameter_defaults.items()}
                                   | load_analysis_parameters(Path(__file__).resolve().parents[1]
                                                              / "data" / "analysis_parameters.csv"))
        for node in ("acc_load", "gear_rate", "acc_resis"):
            selected = MainWindow._required_analysis_rows(window, node)
            self.assertIn("max_load", {row["node_id"] for row in selected})
        gear_tooth_rows = MainWindow._required_analysis_rows(window, "gear_tooth")
        self.assertEqual([row["node_id"] for row in gear_tooth_rows[-5:]],
                         ["max_load", "acc_load", "motor", "gear_rate", "gear_tooth"])
        self.assertIn("cog_movable", {row["node_id"] for row in gear_tooth_rows})

    def test_each_new_plugin_runs_from_shared_vehicle_and_editable_gear_inputs(self):
        params = DEFAULTS | self.motor_outputs | {
            "cog_total_mass_kg": 300.0, "L": 1.53, "h_cog": 0.3,
            "hl_front_weight_ratio": 0.5, "mu_w": 1.7, "R_tire": 0.2,
            "gear_planet_count": 3,
        }
        stages = [
            ("acc_load", {}), ("gear_rate", {}), ("gear_tooth", {}),
            ("number_of_gear", {}), ("output_check", {}), ("rotational_inertia", {}),
            ("acc_resis", {}), ("tooth_strength", {}),
        ]
        for stage, extra in stages:
            plugin = self.plugins[stage]
            result = plugin.run(params | extra)
            try:
                self.assertTrue(result.outputs, stage)
                self.assertTrue(result.tables, stage)
                self.assertTrue(result.figure.axes, stage)
                params.update(result.outputs)
            finally:
                result.close()

    def test_vehicle_mass_is_hidden_and_all_gearing_defaults_are_in_shared_csv(self):
        from pathlib import Path
        from analysis_data import load_analysis_parameters

        values = load_analysis_parameters(Path(__file__).resolve().parents[1]
                                          / "data" / "analysis_parameters.csv")
        for stage in ("acc_load", "gear_rate", "gear_tooth", "number_of_gear", "output_check",
                      "rotational_inertia", "acc_resis", "tooth_strength"):
            self.assertIn("cog_total_mass_kg", self.plugins[stage].hidden_parameters)
        for name, expected in DEFAULTS.items():
            self.assertIn(name, values)
            self.assertAlmostEqual(float(values[name]), float(expected))
        self.assertNotIn("drive_motor_torque_Nm", values)
        self.assertNotIn("drive_motor_torque_Nm", DEFAULTS)

    def test_gear_tooth_runs_without_vehicle_mass(self):
        result = self.plugins["gear_tooth"].run({
            "gear_module_mm": 1.5,
            "gear_ratio_avg": 6.3,
            "gearbox_max_diameter_mm": 180.0,
            "gear_min_teeth": 20,
        })
        try:
            self.assertGreater(result.outputs["gear_candidate_count"], 0)
            self.assertNotIn("cog_total_mass_kg", self.plugins["gear_tooth"].parameters)
            self.assertTrue(result.figure.axes[0].tables)
            table = result.figure.axes[0].tables[0]
            self.assertEqual(len(table.get_celld()), (result.outputs["gear_candidate_count"] + 1) * 5)
            self.assertEqual(set(result.figures), {
                "gear_ratio_distribution.png", "gear_tooth_distribution.png",
            })
        finally:
            result.close()

    def test_number_of_gear_uses_four_manual_tooth_counts(self):
        plugin = self.plugins["number_of_gear"]
        self.assertEqual({name for name in plugin.parameters if name.endswith("_teeth")}, {
            "gear_sun_teeth", "gear_planet1_teeth", "gear_planet2_teeth", "gear_ring_teeth",
        })
        self.assertFalse({"gear_sun_teeth", "gear_planet1_teeth", "gear_planet2_teeth", "gear_ring_teeth"}
                         & plugin.outputs.keys())

    def test_gear_rate_uses_acc_g_and_not_tire_friction_limit(self):
        plugin = self.plugins["gear_rate"]
        base = DEFAULTS | self.motor_outputs | {
            "cog_total_mass_kg": 300.0, "L": 1.53, "h_cog": 0.3,
            "hl_front_weight_ratio": 0.5, "R_tire": 0.2, "acc_g": 1.2,
        }
        first = plugin.run(base | {"mu_w": 0.8})
        second = plugin.run(base | {"mu_w": 2.0})
        try:
            self.assertEqual(first.outputs["gear_ratio_accel"], second.outputs["gear_ratio_accel"])
            self.assertEqual(first.outputs["gear_rate_acceleration_g"], 1.2)
        finally:
            first.close()
            second.close()


if __name__ == "__main__":
    unittest.main()
