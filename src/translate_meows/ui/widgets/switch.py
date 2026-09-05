"""Переключатель-тумблер: рисуется вручную, QCheckBox не даёт нужного вида."""

from typing import Optional

from PyQt6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QSize,
    Qt,
    pyqtProperty,
    pyqtSignal,
)
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QAbstractButton, QWidget

_TRACK_OFF = QColor("#3a3a40")
_TRACK_ON = QColor("#3d5a80")
_KNOB_OFF = QColor("#b8b8bf")
_KNOB_ON = QColor("#ffffff")
_FOCUS = QColor("#5b83b8")

_WIDTH = 34
_HEIGHT = 19
_KNOB = 15
_PADDING = 2


class Switch(QAbstractButton):
    """Тумблер 34×19 с анимацией ручки."""

    toggled_by_user = pyqtSignal(bool)

    def __init__(self, checked: bool = False, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFixedSize(_WIDTH, _HEIGHT)

        self._offset = 1.0 if checked else 0.0
        self._animation = QPropertyAnimation(self, b"offset", self)
        self._animation.setDuration(160)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.clicked.connect(self._on_clicked)

    def sizeHint(self) -> QSize:
        return QSize(_WIDTH, _HEIGHT)

    @pyqtProperty(float)
    def offset(self) -> float:
        return self._offset

    @offset.setter
    def offset(self, value: float) -> None:
        self._offset = value
        self.update()

    def _on_clicked(self, checked: bool) -> None:
        self._animate_to(checked)
        self.toggled_by_user.emit(checked)

    def _animate_to(self, checked: bool) -> None:
        self._animation.stop()
        self._animation.setStartValue(self._offset)
        self._animation.setEndValue(1.0 if checked else 0.0)
        self._animation.start()

    def set_checked_silently(self, checked: bool) -> None:
        """Меняет состояние без сигнала — для синхронизации с настройками."""
        self.setChecked(checked)
        self._animation.stop()
        self.offset = 1.0 if checked else 0.0

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        track = QColor(_TRACK_OFF)
        knob = QColor(_KNOB_OFF)
        if self._offset > 0:
            track = _blend(_TRACK_OFF, _TRACK_ON, self._offset)
            knob = _blend(_KNOB_OFF, _KNOB_ON, self._offset)
        if not self.isEnabled():
            track.setAlpha(110)
            knob.setAlpha(140)

        radius = _HEIGHT / 2
        painter.setBrush(track)
        painter.drawRoundedRect(0, 0, _WIDTH, _HEIGHT, radius, radius)

        travel = _WIDTH - _KNOB - _PADDING * 2
        x = _PADDING + travel * self._offset
        painter.setBrush(knob)
        painter.drawEllipse(int(round(x)), _PADDING, _KNOB, _KNOB)

        if self.hasFocus():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(_FOCUS)
            painter.drawRoundedRect(0, 0, _WIDTH - 1, _HEIGHT - 1, radius, radius)

        painter.end()


def _blend(start: QColor, end: QColor, factor: float) -> QColor:
    factor = max(0.0, min(1.0, factor))
    return QColor(
        int(start.red() + (end.red() - start.red()) * factor),
        int(start.green() + (end.green() - start.green()) * factor),
        int(start.blue() + (end.blue() - start.blue()) * factor),
    )
