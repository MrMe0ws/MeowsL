"""Выбор шрифта интерфейса с fallback-цепочкой."""

from PyQt6.QtGui import QFont, QFontDatabase


def app_font(size: int = 10) -> QFont:
    """Inter → Segoe UI Variable → Segoe UI → Roboto → системный."""
    families = set(QFontDatabase.families())
    for family in (
        "Inter",
        "Segoe UI Variable Text",
        "Segoe UI Variable Display",
        "Segoe UI",
        "Roboto",
    ):
        if family in families:
            font = QFont(family, size)
            font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
            return font
    font = QFont("Segoe UI", size)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    return font
