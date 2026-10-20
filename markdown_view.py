"""Native Markdown notes with SVG formulas painted as vector text objects."""

from dataclasses import dataclass
import re
import xml.etree.ElementTree as ET

from PySide6.QtCore import QByteArray, QSizeF
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPalette,
    QPyTextObject,
    QTextCharFormat,
    QTextFormat,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QTextBrowser

from document_theme import document_colors
from markdown_renderer import svg_display_size


MATH_OBJECT_TYPE = QTextFormat.ObjectTypes.UserObject.value + 1
MATH_ID_PROPERTY = QTextFormat.Property.UserProperty.value + 1
MATH_SVG_PATTERN = re.compile(
    r'<svg\b[^>]*\bclass="math-(?:inline|display)"[^>]*>[\s\S]*?</svg>'
)


@dataclass
class VectorFormula:
    renderer: QSvgRenderer
    size: QSizeF
    source: str
    inline: bool


class VectorMathObject(QPyTextObject):
    """Paint formula paths directly through the document's current painter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.formulas = {}

    def intrinsicSize(self, document, position, char_format):
        formula = self.formulas.get(char_format.stringProperty(MATH_ID_PROPERTY))
        return formula.size if formula is not None else QSizeF()

    def drawObject(self, painter, rect, document, position, char_format):
        formula = self.formulas.get(char_format.stringProperty(MATH_ID_PROPERTY))
        if formula is not None:
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            formula.renderer.render(painter, rect)
            painter.restore()


class MarkdownView(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setOpenExternalLinks(True)
        colors = document_colors()
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor(colors["background"]))
        palette.setColor(QPalette.ColorRole.Text, QColor(colors["foreground"]))
        self.setPalette(palette)
        self.setStyleSheet(
            f"QTextBrowser {{ background: {colors['background']}; "
            f"color: {colors['foreground']}; border: 0; }}"
        )
        self._math_object = VectorMathObject(self)
        self.document().documentLayout().registerHandler(MATH_OBJECT_TYPE, self._math_object)

    def setHtml(self, markup):
        # Qt rich text cannot embed SVG directly. Reserve inline objects in its
        # layout, then let the object handler paint the original vector paths.
        self._math_object.formulas.clear()

        def reserve_formula(match):
            svg_data = match.group(0).encode("utf-8")
            renderer = QSvgRenderer(QByteArray(svg_data))
            if not renderer.isValid():
                return "[無法顯示公式]"
            root = ET.fromstring(svg_data)
            width, height = svg_display_size(svg_data)
            token = f"QTMATHVECTOR{len(self._math_object.formulas)}PLACEHOLDER"
            self._math_object.formulas[token] = VectorFormula(
                renderer=renderer,
                size=QSizeF(width, height),
                source=root.get("aria-label", ""),
                inline=root.get("class") == "math-inline",
            )
            return token

        protected = MATH_SVG_PATTERN.sub(reserve_formula, markup)
        super().setHtml(protected)
        for token, formula in self._math_object.formulas.items():
            cursor = self.document().find(token)
            if cursor.isNull():
                continue
            char_format = cursor.charFormat()
            char_format.setObjectType(MATH_OBJECT_TYPE)
            char_format.setProperty(MATH_ID_PROPERTY, token)
            char_format.setToolTip(formula.source)
            if formula.inline:
                char_format.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignMiddle)
            cursor.insertText("\ufffc", char_format)
