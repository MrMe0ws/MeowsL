"""QComboBox с собственной стрелкой: QSS-треугольник Qt рисует как квадрат."""

from typing import Optional

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QPainter, QPolygonF
from PyQt6.QtWidgets import QComboBox, QWidget

_ARROW = QColor("#8e8e93")
_ARROW_HOVER = QColor("#f2f2f4")
_ARROW_WIDTH = 9.0
_ARROW_HEIGHT = 5.0
_RIGHT_INSET = 11.0


class ArrowComboBox(QComboBox):
    """Выпадающий список тёмной темы с дорисованным шевроном."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def wheelEvent(self, event) -> None:
        """Прокрутка страницы не должна незаметно менять выбранное значение."""
        event.ignore()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(_ARROW_HOVER if self.underMouse() else _ARROW)

        right = self.width() - _RIGHT_INSET
        middle = self.height() / 2 + _ARROW_HEIGHT / 2
        painter.drawPolygon(
            QPolygonF(
                [
                    QPointF(right - _ARROW_WIDTH, middle - _ARROW_HEIGHT),
                    QPointF(right, middle - _ARROW_HEIGHT),
                    QPointF(right - _ARROW_WIDTH / 2, middle),
                ]
            )
        )
        painter.end()
