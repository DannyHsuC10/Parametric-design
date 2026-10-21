"""Regression checks for native vector formulas, notes, and node navigation."""

import os
import json
from pathlib import Path
import re
from types import SimpleNamespace
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QBuffer, QIODevice, QRectF, QSize, QTimer, QUrl
from PySide6.QtGui import QColor, QFontDatabase, QPainter, QPalette, QTextFormat
from PySide6.QtSvg import QSvgGenerator
from PySide6.QtWidgets import QApplication, QDialog, QWidget
from matplotlib import rc_context, rcParams

from main import FlowDiagramPage, MainWindow
from document_theme import document_colors
from markdown_renderer import render_markdown, render_markdown_file
from markdown_view import (
    MATH_ID_PROPERTY,
    MATH_OBJECT_TYPE,
    MATH_SVG_PATTERN,
    MarkdownView,
    VectorMathObject,
)


ROOT = Path(__file__).resolve().parents[1]


class MarkdownRenderingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        if not QFontDatabase.families():
            font = Path("C:/Windows/Fonts/msjh.ttc")
            if font.exists():
                QFontDatabase.addApplicationFont(str(font))

    def assert_vector_formulas(self, view):
        document = view.document()
        handler = document.documentLayout().handlerForObject(MATH_OBJECT_TYPE)
        self.assertIsInstance(handler, VectorMathObject)
        count = 0
        block = document.begin()
        while block.isValid():
            iterator = block.begin()
            while not iterator.atEnd():
                fragment = iterator.fragment()
                fmt = fragment.charFormat()
                self.assertFalse(fmt.isImageFormat())
                if fmt.objectType() == MATH_OBJECT_TYPE:
                    formula = handler.formulas.get(fmt.stringProperty(MATH_ID_PROPERTY))
                    self.assertIsNotNone(formula)
                    self.assertTrue(formula.renderer.isValid())
                    size = handler.intrinsicSize(document, fragment.position(), fmt)
                    self.assertGreater(size.width(), 0)
                    self.assertGreater(size.height(), 0)
                    count += 1
                iterator += 1
            block = block.next()
        return count

    def export_vector_svg(self, view):
        document = view.document()
        document.setTextWidth(800)
        height = document.size().height()
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        generator = QSvgGenerator()
        generator.setOutputDevice(buffer)
        generator.setSize(QSize(800, max(1, round(height))))
        generator.setViewBox(QRectF(0, 0, 800, height))
        painter = QPainter(generator)
        document.drawContents(painter)
        painter.end()
        output = bytes(buffer.data()).decode("utf-8")
        buffer.close()
        return output

    def test_all_saved_notes_display_text_and_formulas(self):
        view = MarkdownView()
        view.resize(800, 900)
        paths = sorted((ROOT / "data" / "results").glob("*/analysis.md"))
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(analysis=path.parent.name):
                rendered = render_markdown(path.read_text(encoding="utf-8-sig"))
                view.setHtml(rendered)
                self.assertGreater(len(view.toPlainText()), 100)
                self.assertEqual(rendered.count("math-source"), 1)
                self.assertEqual(
                    self.assert_vector_formulas(view),
                    len(MATH_SVG_PATTERN.findall(rendered)),
                )
                self.assertNotIn("data:image", rendered)
                self.assertNotIn("QTMATHVECTOR", view.toPlainText())
        view.close()

    def test_node_action_runs_after_navigation_callback_returns(self):
        events = []
        page = SimpleNamespace(
            flowNodeRequested=SimpleNamespace(emit=lambda *args: events.append(args))
        )
        accepted = FlowDiagramPage.acceptNavigationRequest(
            page, QUrl("flow-node://double/frequency_mass"), None, True
        )
        self.assertFalse(accepted)
        self.assertEqual(events, [])
        self.app.processEvents()
        self.assertEqual(events, [("frequency_mass", True)])

    def test_saved_notes_cache_skips_formula_rendering_and_tracks_edits_and_colors(self):
        with TemporaryDirectory(dir=ROOT) as temporary:
            path = Path(temporary) / "analysis.md"
            path.write_text("# Notes\n\n$x^2$", encoding="utf-8")
            info = {}
            first = render_markdown_file(path, cache_info=info)
            self.assertFalse(info["cache_hit"])
            self.assertTrue(path.with_suffix(".rendered.html").is_file())
            with patch("markdown_renderer.render_markdown", side_effect=AssertionError("Unexpected formula rendering")):
                self.assertEqual(render_markdown_file(path, cache_info=info), first)
                self.assertTrue(info["cache_hit"])
            path.write_text("# Edited\n\n$x^3$", encoding="utf-8")
            second = render_markdown_file(path)
            self.assertNotEqual(first, second)
            self.assertIn("Edited", second)
            colors = document_colors() | {"foreground": "#aabbcc"}
            with patch("markdown_renderer.document_colors", return_value=colors):
                themed = render_markdown_file(path)
                self.assertIn("fill: #aabbcc", themed)
                self.assertNotEqual(second, themed)
                with patch("markdown_renderer.render_markdown", side_effect=AssertionError("Unexpected formula rendering")):
                    self.assertEqual(render_markdown_file(path), themed)

    def test_prepared_notes_open_in_result_dialog_without_recompiling_formulas(self):
        path = ROOT / "data" / "results" / "solver_compar" / "analysis.md"
        render_markdown_file(path)
        parent = QWidget()
        with (patch("main.QDialog.exec", return_value=0),
              patch("markdown_renderer.render_markdown", side_effect=AssertionError("Formula recompiled while opening"))):
            MainWindow.show_result(parent, "solver_compar")
        view = parent.findChild(MarkdownView)
        self.assertIsNotNone(view)
        self.assertGreater(self.assert_vector_formulas(view), 0)
        parent.deleteLater()

    def test_flow_request_carries_browser_event_wait_time(self):
        events = []
        page = SimpleNamespace(flowNodeRequested=SimpleNamespace(emit=lambda *args: events.append(args)))
        with patch("main.time", return_value=1000):
            accepted = FlowDiagramPage.acceptNavigationRequest(
                page, QUrl("flow-node://double/frequency_mass?clicked_at=999700"), None, True)
            self.assertFalse(accepted)
            self.assertFalse(events)
            self.app.processEvents()
        self.assertEqual(events, [("frequency_mass", True)])
        self.assertGreaterEqual(page.last_request_delay_ms, 300)

    def test_math_uses_latex_italic_without_changing_plot_defaults(self):
        with rc_context({"mathtext.default": "normal", "mathtext.fontset": "dejavusans"}):
            rendered = render_markdown("$x+1$")
            svg = MATH_SVG_PATTERN.search(rendered).group(0)
            self.assertIn('id="Cmmi10-', svg)
            self.assertIn('id="Cmr10-', svg)
            self.assertEqual(rcParams["mathtext.default"], "normal")
            self.assertEqual(rcParams["mathtext.fontset"], "dejavusans")

    def test_formula_painting_exports_paths_without_bitmap_images(self):
        view = MarkdownView()
        view.setHtml(render_markdown("$$\n\\frac{x+1}{2}\n$$"))
        self.assertEqual(self.assert_vector_formulas(view), 1)
        exported = self.export_vector_svg(view)
        self.assertGreater(len(re.findall(r"<path\b", exported)), 3)
        self.assertNotIn("<image", exported)
        self.assertNotIn("data:image", exported)
        view.close()

    def test_heading_underlines_are_native_horizontal_rules(self):
        view = MarkdownView()
        source = "\n\n".join("#" * level + f" Heading {level}" for level in range(1, 7))
        rendered = render_markdown(source)
        view.setHtml(rendered)
        rules = 0
        block = view.document().begin()
        while block.isValid():
            if block.blockFormat().hasProperty(
                QTextFormat.Property.BlockTrailingHorizontalRulerWidth
            ):
                rules += 1
            block = block.next()
        self.assertEqual(rules, 6)
        self.assertEqual(rendered.count('class="heading-rule"'), 6)
        view.close()

    def test_notes_formulas_and_flow_match_dark_qt_colors(self):
        original_palette = self.app.palette()
        palette = QPalette(original_palette)
        palette.setColor(QPalette.ColorRole.Window, QColor("#24262b"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#eef0f4"))
        palette.setColor(QPalette.ColorRole.Button, QColor("#343840"))
        self.app.setPalette(palette)
        try:
            colors = document_colors()
            self.assertEqual(colors["background"], "#24262b")
            self.assertEqual(colors["foreground"], "#eef0f4")
            view = MarkdownView()
            rendered = render_markdown("# Dark notes\n\n$x^2$")
            view.setHtml(rendered)
            self.assertEqual(
                view.palette().color(QPalette.ColorRole.Base).name(), "#24262b"
            )
            self.assertEqual(self.assert_vector_formulas(view), 1)
            svg = MATH_SVG_PATTERN.search(rendered).group(0)
            self.assertIn("fill: #eef0f4", svg)
            self.assertNotIn("fill: #ffffff", svg)
            exported = self.export_vector_svg(view)
            self.assertIn('fill="#eef0f4"', exported)
            self.assertNotIn("<image", exported)
            flow_html = render_markdown("```mermaid\ngraph TD\nA --> B\n```")
            config = json.loads(
                re.search(r"mermaid.initialize\((\{.*?\})\);", flow_html).group(1)
            )
            self.assertTrue(config["themeVariables"]["darkMode"])
            self.assertEqual(config["themeVariables"]["background"], "#24262b")
            self.assertEqual(config["themeVariables"]["primaryTextColor"], "#eef0f4")
            self.assertEqual(config["themeVariables"]["primaryColor"], "#343840")
            self.assertEqual(config["themeVariables"]["lineColor"], "#ffffff")
            self.assertEqual(config["themeVariables"]["arrowheadColor"], "#ffffff")
            self.assertIn(".mermaid svg marker path", flow_html)
            view.close()
        finally:
            self.app.setPalette(original_palette)

    def test_result_dialog_displays_native_notes(self):
        parent = QWidget()
        parent.add_variable_row = MainWindow.add_variable_row
        errors = []
        inspected = []
        awaiting_first_frame = []

        def inspect_dialog():
            dialog = parent.findChild(QDialog)
            if (dialog is not None and not hasattr(parent, "_last_result_open_timings")
                    and len(awaiting_first_frame) < 100):
                awaiting_first_frame.append(True)
                QTimer.singleShot(20, inspect_dialog)
                return
            try:
                self.assertIsNotNone(dialog)
                view = dialog.findChild(MarkdownView)
                self.assertIsNotNone(view)
                self.assertTrue(view.isVisible())
                self.assertGreater(view.width(), 100)
                self.assertIn("Frequency vs mass", view.toPlainText())
                self.assertGreater(self.assert_vector_formulas(view), 0)
                timings = parent._last_result_open_timings
                self.assertEqual(timings["node_id"], "frequency_mass")
                self.assertGreaterEqual(timings["first_frame_ms"], timings["prepare_ms"])
                inspected.append(True)
            except BaseException as error:
                errors.append(error)
            finally:
                if dialog is not None:
                    dialog.accept()

        QTimer.singleShot(100, inspect_dialog)
        MainWindow.show_result(parent, "frequency_mass")
        parent.close()
        if errors:
            raise errors[0]
        self.assertTrue(inspected)


if __name__ == "__main__":
    unittest.main()
