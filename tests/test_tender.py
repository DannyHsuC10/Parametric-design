"""Verify the tender binds at the specified whole-vehicle downforce."""

from contextlib import redirect_stdout
from io import StringIO
import unittest
from unittest.mock import patch

import matplotlib
matplotlib.use("Agg")

from analysis import tender


class TenderSwitchTests(unittest.TestCase):
    def test_switch_force_and_response_at_vehicle_downforce_target(self):
        for ratio in (0.0, 0.5, 1.0):
            with self.subTest(ratio=ratio):
                parameters = dict(ms=260, mu=14, K_heave_main_N_per_m=150000,
                                  tender_to_heave_stiffness_ratio=0.5,
                                  aero_cl_cd_F_ref_N=400, F_ref_ratio=ratio,
                                  anti_geometry_ratio=0.2, L=1.5, h_cog=0.3)
                residuals = []
                solve = tender.root

                def record_residual(residual, guess):
                    residuals.append(residual)
                    return solve(residual, guess)

                with patch.object(tender, "root", side_effect=record_residual), redirect_stdout(StringIO()):
                    result = tender.main(parameters)
                try:
                    outputs = result.outputs
                    self.assertEqual(set(outputs), set(tender.OUTPUTS))
                    target = 400 * ratio
                    self.assertAlmostEqual(outputs["tender_bind_vehicle_downforce_N"], target)
                    self.assertAlmostEqual(outputs["tender_bind_force_N"], target / 2)
                    self.assertAlmostEqual(outputs["tender_bind_spring_stroke_mm"], target / 2 / 75)
                    stroke = outputs["tender_bind_total_stroke_mm"]
                    self.assertAlmostEqual(stroke, target / 2 / 50)

                    # Last curve is the target downforce; its first point has
                    # zero braking. Both assemblies must balance at the switch.
                    residual = residuals[4 * 41]
                    self.assertAlmostEqual(residual([stroke, stroke])[0], 0)
                    self.assertAlmostEqual(residual([stroke, stroke])[1], 0)
                    baseline = residual([0, 0])[0]

                    def force(value):
                        return residual([value, 0])[0] - baseline

                    # Check force continuity and tangent stiffness on both sides.
                    step = 1e-4
                    self.assertAlmostEqual(force(stroke), target / 2)
                    self.assertAlmostEqual((force(stroke) - force(stroke - step)) / step, 50)
                    self.assertAlmostEqual((force(stroke + step) - force(stroke)) / step, 150)
                finally:
                    result.close()


if __name__ == "__main__":
    unittest.main()
