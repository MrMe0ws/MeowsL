"""Иконка приложения из photo/logo.png."""

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QImage, QPainter, QPixmap

from translate_meows.paths import asset_path

_PHOTO_DIR = asset_path("photo")
_LOGO_CANDIDATES = (
    _PHOTO_DIR / "logo-icon.ico",
    _PHOTO_DIR / "logo-icon.png",
    _PHOTO_DIR / "logo.png",
)
_ICON_SIZES = (16, 24, 32, 48, 64, 128, 256)


def _fallback_icon() -> QIcon:
    """Запасная иконка «T», если logo.png недоступен."""
    size = 64
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(QColor(0, 0, 0, 0))

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(90, 90, 95))
    painter.setPen(QColor(200, 200, 205))
    painter.drawRoundedRect(4, 4, size - 8, size - 8, 12, 12)
    painter.setPen(QColor(255, 255, 255))
    font = painter.font()
    font.setPixelSize(36)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(image.rect(), int(Qt.AlignmentFlag.AlignCenter), "T")
    painter.end()

    return QIcon(QPixmap.fromImage(image))


def _logo_path() -> Path | None:
    for candidate in _LOGO_CANDIDATES:
        if candidate.is_file():
            return candidate
    return None


def app_icon() -> QIcon:
    """Возвращает иконку приложения для трея и окон."""
    path = _logo_path()
    if path is None:
        return _fallback_icon()

    if path.suffix.lower() == ".ico":
        icon = QIcon(str(path))
        if not icon.isNull():
            return icon

    source = QPixmap(str(path))
    if source.isNull():
        return _fallback_icon()

    icon = QIcon()
    for size in _ICON_SIZES:
        icon.addPixmap(
            source.scaled(
                size,
                size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
    return icon


def logo_pixmap(size: int) -> QPixmap:
    """Логотип нужного размера для шапки главного окна."""
    pixmap = app_icon().pixmap(size, size)
    if not pixmap.isNull():
        return pixmap
    return _fallback_icon().pixmap(size, size)
