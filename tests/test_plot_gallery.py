"""Keep all analysis plots readable and expose every exported page in the gallery."""

import csv
from contextlib import redirect_stdout
from io import StringIO
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QComboBox, QDialog, QWidget

from analysis_data import load_analysis_parameters, parse_analysis_parameters
from analysis_result import load_plot_choices, normalize_result, save_analysis_result
from main import MainWindow, ScalableImageLabel
from plugin_loader import scan_analysis

ROOT = Path(__file__).resolve().parents[1]


class PlotGalleryTests(unittest.TestCase):
    def test_every_analysis_has_at_most_four_axes_and_preserves_all_panels(self):
        values = load_analysis_parameters(ROOT / "data" / "analysis_parameters.csv")
        plugins = {plugin.plugin_id: plugin for plugin in scan_analysis()}
        expected = {"time_sensitivity": [4, 4, 4], "damping_rate": [1, 3, 3, 3],
                    "psd": [3, 3, 3], "tender": [4, 1]}
        with (ROOT / "data" / "analysis_flow.csv").open(encoding="utf-8-sig", newline="") as stream:
            flow = list(csv.DictReader(stream))
        self.assertEqual(set(plugins), {row["analysis_id"] for row in flow})
        observed = {}
        with redirect_stdout(StringIO()):
            for row in flow:
                plugin = plugins[row["analysis_id"]]
                result = normalize_result(plugin.run(parse_analysis_parameters(values, plugin.parameters)))
                try:
                    figures = list({id(figure): figure for figure in (result.figure, *result.figures.values())}.values())
                    counts = [len(figure.axes) for figure in figures]
                    self.assertTrue(all(1 <= count <= 4 for count in counts), (plugin.plugin_id, counts))
                    if plugin.plugin_id in expected:
                        self.assertEqual(counts, expected[plugin.plugin_id])
                        for figure in figures:
                            for axis in figure.axes:
                                self.assertTrue(axis.has_data(), (plugin.plugin_id, axis.get_title()))
                        observed[plugin.plugin_id] = counts
                    values.update({key: str(value) for key, value in result.outputs.items()})
                finally:
                    result.close()
        self.assertEqual(observed, expected)

    def test_exported_pages_switch_in_result_dialog_and_ignore_old_images(self):
        plugin = next(plugin for plugin in scan_analysis() if plugin.plugin_id == "psd")
        with redirect_stdout(StringIO()):
            result = normalize_result(plugin.run({}))
        try:
            with TemporaryDirectory(dir=ROOT) as temporary:
                destination = Path(temporary).resolve()
                self.assertTrue(destination.is_relative_to(ROOT.resolve()))
                save_analysis_result(destination, "psd", {}, result)
                (destination / "psd" / "old_combined_plot.png").write_bytes(b"old image")
                choices = load_plot_choices(destination / "psd")
                self.assertEqual([filename for _, filename in choices], [
                    "plot.png", "road_profile_fft.png", "vehicle_speed_distribution.png"])
                self.assertEqual(choices[0][0], "主要結果｜激振頻譜與能量")
                self.assertTrue(all((destination / "psd" / filename).is_file() for _, filename in choices))
                app = QApplication.instance() or QApplication([])
                parent = QWidget()
                checked, errors = [], []

                def inspect():
                    dialog = parent.findChild(QDialog)
                    try:
                        self.assertIsNotNone(dialog)
                        selector = dialog.findChildren(QComboBox)[0]
                        self.assertEqual(selector.count(), 3)
                        image = dialog.findChild(ScalableImageLabel)
                        for index, (title, filename) in enumerate(choices):
                            selector.setCurrentIndex(index)
                            self.assertEqual(selector.currentText(), title)
                            self.assertEqual(selector.currentData(), filename)
                            self.assertFalse(image.original_pixmap.isNull())
                        checked.append(True)
                    except BaseException as error:
                        errors.append(error)
                    finally:
                        if dialog is not None:
                            dialog.accept()

                with patch("main.RESULTS_DIR", destination):
                    QTimer.singleShot(100, inspect)
                    MainWindow.show_result(parent, "psd")
                parent.close()
                if errors:
                    raise errors[0]
                self.assertTrue(checked)
        finally:
            result.close()

    def test_old_result_directories_still_have_a_gallery(self):
        with TemporaryDirectory(dir=ROOT) as temporary:
            folder = Path(temporary).resolve()
            self.assertTrue(folder.is_relative_to(ROOT.resolve()))
            for name in ("plot.png", "extra.png"):
                (folder / name).write_bytes(b"saved image")
            self.assertEqual(load_plot_choices(folder), [("主要結果", "plot.png"), ("extra", "extra.png")])


if __name__ == "__main__":
    unittest.main()
