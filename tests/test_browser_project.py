"""Round-trip tests for the JSON files handled by the web workbench."""

import json
import unittest

from browser_app import handle_request
from project import default_project


def request(action, payload):
    return json.loads(handle_request(action, json.dumps(payload)))


class BrowserProjectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parameters = default_project() | {
            "ms": 272,
            "A_air": 1.1,
            "drive_motor_rpm": 16000,
            "target_sprung_frequency_Hz": 3.2,
        }
        cls.dynamics_json = request("solve", {
            "parameters": cls.parameters,
            "name": "Round-trip",
        })["result"]["dynamics"]

    def test_saved_project_can_be_imported(self):
        saved = request("save", self.parameters)["result"]
        self.assertEqual(request("import", "\ufeff" + saved)["result"]["parameters"], self.parameters)

    def test_dynamics_export_restores_all_inputs(self):
        restored = request("import", self.dynamics_json)["result"]
        self.assertEqual(restored["parameters"], self.parameters)
        self.assertTrue(restored["is_dynamics"])
        self.assertFalse(restored["used_defaults"])

    def test_legacy_dynamics_import_fills_missing_inputs(self):
        document = json.loads(self.dynamics_json)
        del document["source_project"]
        for version in (2, 3):
            with self.subTest(version=version):
                document["schema_version"] = version
                restored = request("import", json.dumps(document))["result"]
                self.assertTrue(restored["used_defaults"])
                self.assertEqual(restored["parameters"]["ms"], self.parameters["ms"])
                self.assertAlmostEqual(
                    restored["parameters"]["min_turn_radius_m"], self.parameters["min_turn_radius_m"]
                )
                self.assertEqual(restored["parameters"]["drive_motor_rpm"], default_project()["drive_motor_rpm"])

    def test_unknown_dynamics_version_is_rejected(self):
        document = json.loads(self.dynamics_json)
        document["schema_version"] = 999
        self.assertIn("error", request("import", json.dumps(document)))


if __name__ == "__main__":
    unittest.main()
