"""Сохранение размера и позиции popup между сессиями."""

from PyQt6.QtCore import QByteArray, QSettings
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QWidget

from translate_meows.config import (
    POPUP_HEIGHT,
    POPUP_WIDTH,
    SETTINGS_APP,
    SETTINGS_KEY_POPUP_GEOMETRY,
    SETTINGS_ORG,
)


def load_popup_geometry(widget: QWidget) -> bool:
    settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
    raw = settings.value(SETTINGS_KEY_POPUP_GEOMETRY)
    if not isinstance(raw, QByteArray) or raw.isEmpty():
        return False
    if not widget.restoreGeometry(raw):
        return False
    if widget.size().isEmpty():
        return False
    return True


def save_popup_geometry(widget: QWidget) -> None:
    settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
    settings.setValue(SETTINGS_KEY_POPUP_GEOMETRY, widget.saveGeometry())
    settings.sync()


def ensure_popup_on_screen(widget: QWidget) -> None:
    """Не даёт окну оказаться полностью за пределами доступной области экрана."""
    center = widget.frameGeometry().center()
    screen = QGuiApplication.screenAt(center) or QGuiApplication.primaryScreen()
    if screen is None:
        return

    available = screen.availableGeometry()
    geo = widget.frameGeometry()
    max_x = available.right() - geo.width() + 1
    max_y = available.bottom() - geo.height() + 1
    x = max(available.left(), min(geo.x(), max_x))
    y = max(available.top(), min(geo.y(), max_y))
    if x != geo.x() or y != geo.y():
        widget.move(x, y)


def center_popup_on_screen(widget: QWidget) -> None:
    """Центрирует окно на доступной области экрана."""
    widget.resize(POPUP_WIDTH, POPUP_HEIGHT)

    screen = QGuiApplication.screenAt(widget.frameGeometry().center())
    if screen is None:
        screen = QGuiApplication.primaryScreen()
    if screen is None:
        return

    available = screen.availableGeometry()
    frame = widget.frameGeometry()
    widget.move(
        available.x() + max(0, (available.width() - frame.width()) // 2),
        available.y() + max(0, (available.height() - frame.height()) // 2),
    )
