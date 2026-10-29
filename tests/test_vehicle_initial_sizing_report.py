"""The generated Markdown must describe the current run and update after parameter changes."""

from contextlib import redirect_stdout
from io import StringIO
import math
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Initial settings"))

import vehicle_initial_sizing as model
from vehicle_initial_sizing_report import render_markdown_report, write_markdown_report


class MarkdownReportTests(unittest.TestCase):
    def run_report(self, path):
        output = StringIO()
        with redirect_stdout(output):
            snapshot = model.main(report_path=path)
        return snapshot, path.read_text(encoding="utf-8"), output.getvalue()

    def test_generated_equations_keep_latex_spacing_commands_separate(self):
        for enabled, divisor in ((True, 5.), (False, 0.), (True, 3.)):
            with (self.subTest(use_tender=enabled, N=divisor),
                  patch.multiple(model, use_tender=enabled, N=divisor),
                  redirect_stdout(StringIO())):
                text = render_markdown_report(model.main(write_report=False))
            equations = re.findall(r"\$\$\n(.*?)\n\$\$", text, re.DOTALL)
            self.assertGreater(len(equations), 100)
            for equation in equations:
                # Adjacent Python literals must not merge a TeX command with its next variable.
                self.assertNotRegex(equation, r"\\(?:quad|qquad)[A-Za-z]")

    def test_full_report_uses_the_same_calculation_run_as_stdout(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "report.md"
            with patch.object(model, "calculate_skidpad_downforce", wraps=model.calculate_skidpad_downforce) as skidpad:
                snapshot, text, output = self.run_report(path)
            skidpad.assert_called_once()
            self.assertIn("Markdown 計算報告已更新", output)
            self.assertIn("Roll & Pitch gradient", output)
            self.assertIn("graph TD", text)
            for heading in ("## 0.", "## 1.", "## 2.", "## 3.", "## 4.", "## 5.", "## 6.", "## 7.",
                            "## 8.", "## 9.", "## 9.3", "## 10.", "## 11.1", "## 11.2", "## 11.3",
                            "## 12.", "## 13.", "## 14.", "## 15.", "## 16.", "## 17.", "## 18.", "## 19.", "## 20."):
                self.assertIn(heading, text)
            self.assertIn(r"M=260.55+4\cdot14.4=318.15", text)
            self.assertIn(format(snapshot["caster"]["caster_deg"], ".12g"), text)
            self.assertIn(format(snapshot["gradients"]["roll_gradient_with_tires_deg_per_g"], ".12g"), text)
            self.assertGreater(text.count("$$"), 500)
            self.assertEqual(text.count("$$") % 2, 0)
            self.assertEqual(text.count("```") % 2, 0)
            self.assertIsNone(re.search(r"@[A-Za-z_][A-Za-z_0-9]*@", text))
            self.assertEqual(list(path.parent.glob("*.tmp")), [])

    def test_rerun_overwrites_report_and_updates_weight_geometry_and_derived_results(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "report.md"
            original, old_text, _ = self.run_report(path)
            path.write_text(old_text + "\nOUTDATED_SENTINEL", encoding="utf-8")
            with patch.multiple(model, ms=300., lf=.7, lr=.8, min_turn_radius_m=2.7):
                changed, text, _ = self.run_report(path)
            self.assertNotIn("OUTDATED_SENTINEL", text)
            self.assertNotEqual(old_text, text)
            self.assertIn("| ms | 300 |", text)
            self.assertIn(r"M=300+4\cdot14.4=357.6", text)
            self.assertIn(r"L=0.7+0.8=1.5", text)
            self.assertIn(format(math.degrees(math.atan(1.5 / 2.7)), ".12g"), text)
            for group, key in (("skidpad", "skidpad_required_aero_downforce_N"),
                               ("tire", "Ks_pitch_N_per_m"),
                               ("caster", "caster_deg")):
                self.assertNotEqual(original[group][key], changed[group][key])
                self.assertIn(format(changed[group][key], ".12g"), text)
            self.assertEqual(original["parameters"]["ms"], 260.55)
            self.assertEqual(changed["parameters"]["ms"], 300.)

    def test_unavailable_tender_is_explicit_and_independent_results_are_kept(self):
        with TemporaryDirectory() as directory, patch.object(model, "N", 3.):
            snapshot, text, _ = self.run_report(Path(directory) / "report.md")
        self.assertIsNone(snapshot["tender"])
        self.assertIn("Tender 無可行解", text)
        self.assertIn("| front.combined_average | —（無可用解） |", text)
        self.assertIn("| rear.heave_with_tender | —（無可用解） |", text)
        self.assertIn("後軸：Kheaveonly", text)
        self.assertIn("Roll 與 Pitch gradient", text)
        self.assertIn(format(snapshot["gradients"]["roll_gradient_with_tires_deg_per_g"], ".12g"), text)

    def test_contact_flags_and_failed_caster_are_not_rendered_as_physical_zero_solutions(self):
        with redirect_stdout(StringIO()):
            default = model.main(write_report=False)
            with patch.object(model, "ay", 1.):
                valid = model.main(write_report=False)
        default_text = render_markdown_report(default)
        self.assertIn("Caster 算式有實數解，接地模型失效", default_text)
        self.assertIn("負壓縮及 Roll 為線性外推參考", default_text)
        valid_text = render_markdown_report(valid)
        self.assertIn("**接地有效。**", valid_text)
        self.assertNotIn("Caster 算式有實數解，接地模型失效", valid_text)
        valid["caster"] = model.calculate_caster_for_zero_camber(90., 0., 0., 8., 1.)
        valid["parameters"]["steering_angle_deg"] = 1.
        failed = render_markdown_report(valid)
        self.assertIn("Caster 狀態：unreachable", failed)
        self.assertIn("無實數解", failed)
        self.assertIn("| final_camber_deg | —（無可用解） |", failed)

    def test_disabled_tender_report_uses_main_spring_and_replaces_previous_tender_results(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "report.md"
            _, enabled_text, _ = self.run_report(path)
            self.assertIn("### Heave + Tender", enabled_text)
            with patch.multiple(model, use_tender=False, N=0.):
                snapshot, text, output = self.run_report(path)
        main = snapshot["tire"]["Ks_pitch_N_per_m"]
        self.assertIn("| use_tender | 否 |", text)
        self.assertIn("Tender 已關閉", text)
        self.assertIn("Tender 已關閉", output)
        self.assertNotIn("Tender 無可行解", text)
        self.assertNotIn("無可行正 Heave 解", text)
        self.assertNotIn("### Heave + Tender", text)
        self.assertNotIn("### Pitch：Heave + Tender", text)
        self.assertNotIn(r"K_{h,\mathrm{target}}=", text)
        self.assertIn("前軸：(Kheave + Kroll)/2", text)
        self.assertIn("後軸：Kheave", text)
        self.assertIn("### Pitch：純 Heave", text)
        self.assertIn(format(main, ".12g"), text)
        self.assertEqual(text.count("$$") % 2, 0)
        self.assertIsNone(re.search(r"@[A-Za-z_][A-Za-z_0-9]*@", text))

    def test_invalid_parameters_or_render_failure_preserve_last_completed_report(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "report.md"
            path.write_text("LAST_COMPLETE_REPORT", encoding="utf-8")
            with patch.object(model, "min_turn_radius_m", 0.), self.assertRaises(ValueError):
                model.main(report_path=path)
            self.assertEqual(path.read_text(encoding="utf-8"), "LAST_COMPLETE_REPORT")
            with patch("vehicle_initial_sizing_report.render_markdown_report", side_effect=ValueError("render failed")):
                with self.assertRaises(ValueError):
                    write_markdown_report({}, path)
            self.assertEqual(path.read_text(encoding="utf-8"), "LAST_COMPLETE_REPORT")


if __name__ == "__main__":
    unittest.main()

