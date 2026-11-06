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
from urllib.parse import unquote, urlsplit
from urllib.request import url2pathname

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Initial settings"))

import vehicle_initial_sizing as model
from vehicle_initial_sizing_report import render_markdown_report, split_markdown_report, write_markdown_report


REPORT_CHAPTERS = {
    "01_inputs_cg.md": ("0.", "1."),
    "02_skidpad_aero.md": ("2.", "2.4"),
    "03_suspension_stiffness.md": ("3.", "4.", "5.", "6.", "7.", "8.", "9."),
    "04_geometry_steering.md": ("9.3", "10.", "11.1", "11.2", "11.3"),
    "05_aero_wheel_loads.md": ("12.", "13."),
    "06_drivetrain_braking.md": ("14.", "15.", "16."),
    "07_critical_damping.md": ("17.",),
    "08_spring_rate_cases.md": ("18.",),
    "09_roll_pitch_gradients.md": ("19.",),
    "10_results_index.md": ("20.",),
}


class MarkdownReportTests(unittest.TestCase):
    def read_report_bundle(self, path):
        files = {path.name: path.read_text(encoding="utf-8")}
        files.update((name, (path.parent / name).read_text(encoding="utf-8")) for name in REPORT_CHAPTERS)
        return files

    def run_report(self, path):
        output = StringIO()
        with redirect_stdout(output):
            snapshot = model.main(report_path=path)
        return snapshot, "\n".join(self.read_report_bundle(path).values()), output.getvalue()

    def test_split_preserves_every_original_section_once_in_its_category(self):
        for enabled, divisor in ((True, 5.), (False, 0.), (True, 3.)):
            with (self.subTest(use_tender=enabled, N=divisor),
                  patch.multiple(model, use_tender=enabled, N=divisor),
                  redirect_stdout(StringIO())):
                original = render_markdown_report(model.main(write_report=False))
            files = split_markdown_report(original)
            self.assertEqual(set(files), {"README.md", *REPORT_CHAPTERS})
            complete = "\n".join(files.values())
            first_section = original.index("## 0.")
            self.assertIn(original[:first_section], files["README.md"])
            sections = list(re.finditer(r"^## (\d+(?:\.\d+)?\.?) .*$", original, re.MULTILINE))
            expected = {number: filename for filename, numbers in REPORT_CHAPTERS.items() for number in numbers}
            expected["21."] = "README.md"
            self.assertEqual({match.group(1) for match in sections}, set(expected))
            for index, match in enumerate(sections):
                end = sections[index + 1].start() if index + 1 < len(sections) else len(original)
                section = original[match.start():end]
                self.assertIn(section, files[expected[match.group(1)]])
                self.assertEqual(complete.count(section), 1, match.group(0))
            for name, text in files.items():
                self.assertEqual(text.count("$$") % 2, 0, name)
                self.assertEqual(text.count("```") % 2, 0, name)
            self.assertLess(len(files["README.md"]), len(original) // 8)

    def test_split_rejects_unclassified_and_duplicate_sections(self):
        with redirect_stdout(StringIO()):
            original = render_markdown_report(model.main(write_report=False))
        for extra in ("## 22. 未分類章節\n\n保留內容\n\n", "## 0. 重複輸入\n\n重複內容\n\n",
                      "## 22. 未分類章節", "## 0. 重複輸入"):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                split_markdown_report(original + extra)

    def test_main_report_and_chapter_links_work_for_custom_nested_output(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "自訂 目錄" / "nested" / "主報告.md"
            self.run_report(path)
            files = self.read_report_bundle(path)
            self.assertEqual(set(child.name for child in path.parent.iterdir()), set(files))
            self.assertIn("graph TD", files[path.name])
            self.assertIn("## 21. 更新方式", files[path.name])
            self.assertNotIn("## 0.", files[path.name])
            source = Path(model.__file__).with_name("vehicle_initial_sizing_calculations.md").resolve()
            links_to_model = []
            for name, text in files.items():
                links = re.findall(r"\[[^\]]*\]\((?:<([^>]+)>|([^\)]+))\)", text)
                resolved = []
                for angle_target, plain_target in links:
                    target = angle_target or plain_target
                    parsed = urlsplit(target)
                    if parsed.scheme == "file":
                        destination = Path(url2pathname(parsed.path)).resolve()
                    elif parsed.scheme or parsed.netloc or not parsed.path:
                        continue
                    else:
                        self.assertFalse(Path(unquote(parsed.path)).is_absolute(), target)
                        destination = (path.parent / unquote(parsed.path)).resolve()
                    self.assertTrue(destination.exists(), f"{name}: {target}")
                    resolved.append(destination)
                    if destination == source:
                        links_to_model.append((name, target))
                if name == path.name:
                    for chapter in REPORT_CHAPTERS:
                        self.assertIn((path.parent / chapter).resolve(), resolved)
                else:
                    self.assertIn(path.resolve(), resolved, name)
            self.assertTrue(links_to_model)

    def test_default_report_is_written_into_a_dedicated_subdirectory(self):
        self.assertEqual(model.DEFAULT_REPORT_PATH,
                         Path(model.__file__).with_name("vehicle_initial_sizing_report") / "README.md")

    def test_model_explanation_link_is_relative_on_the_same_drive(self):
        source_directory = Path(model.__file__).parent
        with TemporaryDirectory(dir=source_directory) as directory:
            path = Path(directory) / "nested" / "deeper" / "README.md"
            self.run_report(path)
            text = path.read_text(encoding="utf-8")
            links = re.findall(r"\[計算說明\]\((?:<([^>]+)>|([^\)]+))\)", text)
            self.assertEqual(len(links), 1)
            target = next(value for value in links[0] if value)
            self.assertFalse(urlsplit(target).scheme)
            self.assertEqual((path.parent / unquote(target)).resolve(),
                             (source_directory / "vehicle_initial_sizing_calculations.md").resolve())

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
            for name, content in self.read_report_bundle(path).items():
                (path.parent / name).write_text(content + "\nOUTDATED_SENTINEL", encoding="utf-8")
            with patch.multiple(model, ms=300., lf=.7, lr=.8, min_turn_radius_m=2.7):
                changed, text, _ = self.run_report(path)
            self.assertNotIn("OUTDATED_SENTINEL", text)
            for name, content in self.read_report_bundle(path).items():
                self.assertNotIn("OUTDATED_SENTINEL", content, name)
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
            self.assertEqual(list(path.parent.glob("*.tmp")), [])

    def test_unavailable_tender_is_explicit_and_independent_results_are_kept(self):
        with TemporaryDirectory() as directory, patch.multiple(model, N=3., target_pitch_angle_deg=1.):
            snapshot, text, _ = self.run_report(Path(directory) / "report.md")
        self.assertIsNone(snapshot["tender"])
        self.assertEqual(set(snapshot["anti"]), {"heave_only"})
        self.assertIsNotNone(snapshot["anti"]["heave_only"])
        self.assertIn("Tender 無可行解", text)
        self.assertIn("| front.combined_average | —（無可用解） |", text)
        self.assertIn("| rear.heave_with_tender | —（無可用解） |", text)
        self.assertIn("後軸：Kheaveonly", text)
        self.assertIn("Roll 與 Pitch gradient", text)
        self.assertIn(format(snapshot["gradients"]["roll_gradient_with_tires_deg_per_g"], ".12g"), text)

    def test_report_uses_each_axles_stiffness_anti_and_refreshes_independent_chassis_inputs(self):
        with (TemporaryDirectory() as directory,
              patch.multiple(model, use_tender=True, anti_front_chassis_stiffness_N_per_m=400000.,
                             anti_rear_chassis_stiffness_N_per_m=800000.)):
            path = Path(directory) / "report.md"
            original, text, output = self.run_report(path)
            files = self.read_report_bundle(path)
            geometry = files["04_geometry_steering.md"]
            self.assertIn("## 9.3 前 Anti-dive 與 9.4 AntiScrub／前後 Anti-lift", geometry)
            self.assertIn("| anti_front_chassis_stiffness_N_per_m | 400000 |", text)
            self.assertIn("| anti_rear_chassis_stiffness_N_per_m | 800000 |", text)
            self.assertIn("AntiScrub", text)
            self.assertIn("heave_only.anti_scrub_ratio", files["10_results_index.md"])
            self.assertNotIn("### anti_dive", text)
            self.assertIn("AntiScrub", output)
            self.assertEqual(set(original["anti"]), {"heave_only"})
            anti_section = geometry.split("## 9.3 ", 1)[1].split("## 10.", 1)[0]
            self.assertNotIn("### Heave + Tender", anti_section)
            for axle in ("front", "rear"):
                anti = original["anti"]["heave_only"][axle]
                self.assertIn(format(anti["anti_ratio"], ".12g"), geometry)
                self.assertIn(f"heave_only.{axle}.anti_ratio", files["10_results_index.md"])
                self.assertNotIn(f"heave_with_tender.{axle}.anti_ratio", files["10_results_index.md"])
            mapping = original["anti"]["heave_only"]
            self.assertNotEqual(mapping["front"]["anti_ratio"], mapping["rear"]["anti_ratio"])
            self.assertEqual(mapping["rear_anti_lift_ratio"], mapping["front_anti_dive_ratio"])
            self.assertEqual(mapping["front_anti_lift_ratio"], mapping["anti_scrub_ratio"])
            for name in ("front_anti_dive", "rear_anti_lift", "anti_scrub", "front_anti_lift"):
                self.assertIn(f"heave_only.{name}_ratio", files["10_results_index.md"])
                self.assertIn(format(mapping[f"{name}_ratio"], ".12g"), geometry)
            values = original["gradients"]["pitch"]["heave_only"]
            self.assertIn(r"(1-\mathrm{AntiDive}_f)G_{s,f}+(1-\mathrm{AntiLift}_r)G_{s,r}",
                          files["09_roll_pitch_gradients.md"])
            self.assertIn(format(values["gradient_with_tires_and_anti_deg_per_g"], ".12g"),
                          files["09_roll_pitch_gradients.md"])
            series_values = original["gradients"]["pitch"]["heave_with_tender"]
            self.assertNotIn("gradient_with_tires_and_anti_deg_per_g", series_values)
            series_pitch = files["09_roll_pitch_gradients.md"].split("### Pitch：Heave + Tender", 1)[1]
            series_pitch = series_pitch.split("### Pitch：純 Heave", 1)[0]
            self.assertIn(format(series_values["gradient_with_tires_deg_per_g"], ".12g"), series_pitch)
            self.assertNotIn(r"G_{\mathrm{pitch,anti}}", series_pitch)

            # Existing chapter files from the previous format must lose their series Anti rows on rerun.
            stale = "\nLEGACY_SERIES_ANTI\n| heave_with_tender.front.anti_ratio | 0.25 |\n"
            for filename in ("04_geometry_steering.md", "09_roll_pitch_gradients.md", "10_results_index.md"):
                (path.parent / filename).write_text(files[filename] + stale, encoding="utf-8")
            with patch.object(model, "anti_rear_chassis_stiffness_N_per_m", 1200000.):
                changed, updated, _ = self.run_report(path)
            self.assertEqual(set(changed["anti"]), {"heave_only"})
            self.assertEqual(changed["anti"]["heave_only"]["front"], original["anti"]["heave_only"]["front"])
            self.assertLess(changed["anti"]["heave_only"]["rear"]["anti_ratio"],
                            original["anti"]["heave_only"]["rear"]["anti_ratio"])
            for field in ("front_anti_dive_ratio", "rear_anti_lift_ratio"):
                self.assertEqual(changed["anti"]["heave_only"][field], mapping[field])
            for field in ("anti_scrub_ratio", "front_anti_lift_ratio"):
                self.assertLess(changed["anti"]["heave_only"][field], mapping[field])
            self.assertEqual(changed["gradients"]["pitch"]["heave_only"]["gradient_with_tires_and_anti_deg_per_g"],
                             values["gradient_with_tires_and_anti_deg_per_g"])
            self.assertEqual(changed["gradients"]["pitch"]["heave_with_tender"], series_values)
            self.assertNotIn("LEGACY_SERIES_ANTI", updated)
            self.assertNotIn("heave_with_tender.front.anti_ratio", updated)
            self.assertIn("| anti_rear_chassis_stiffness_N_per_m | 1200000 |", updated)
            self.assertNotEqual(self.read_report_bundle(path)["04_geometry_steering.md"], geometry)

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
        self.assertEqual(set(snapshot["anti"]), {"heave_only"})
        self.assertIsNotNone(snapshot["anti"]["heave_only"])
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
            self.run_report(path)
            previous = self.read_report_bundle(path)
            with patch.object(model, "min_turn_radius_m", 0.), self.assertRaises(ValueError):
                model.main(report_path=path)
            self.assertEqual(self.read_report_bundle(path), previous)
            with patch("vehicle_initial_sizing_report.render_markdown_report", side_effect=ValueError("render failed")):
                with self.assertRaises(ValueError):
                    write_markdown_report({}, path)
            self.assertEqual(self.read_report_bundle(path), previous)
            with patch("vehicle_initial_sizing_report.split_markdown_report", side_effect=ValueError("split failed")):
                with self.assertRaises(ValueError):
                    with redirect_stdout(StringIO()):
                        model.main(report_path=path)
            self.assertEqual(self.read_report_bundle(path), previous)
            self.assertEqual(set(child.name for child in path.parent.iterdir()), set(previous))


if __name__ == "__main__":
    unittest.main()

