"""Shared dark colors for native Markdown notes and the web flow diagram."""

from PySide6.QtGui import QGuiApplication, QPalette


def document_colors():
    colors = {
        "background": "#202020",
        "foreground": "#eeeeee",
        "surface": "#303030",
        "border": "#646464",
        "accent": "#9acbff",
        "error": "#ffb4ab",
    }
    application = QGuiApplication.instance()
    if application is not None:
        palette = application.palette()
        background = palette.color(QPalette.ColorRole.Window)
        foreground = palette.color(QPalette.ColorRole.WindowText)
        if background.lightness() < 128 and foreground.lightness() > 128:
            colors["background"] = background.name()
            colors["foreground"] = foreground.name()
            surface = palette.color(QPalette.ColorRole.Button)
            if surface.lightness() < 128:
                colors["surface"] = surface.name()
            accent = palette.color(QPalette.ColorRole.Link)
            if accent.lightness() >= 128:
                colors["accent"] = accent.name()
    return colors
