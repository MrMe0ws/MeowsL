"""Верхняя полоса — название слева и зона перетаскивания."""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget

from translate_meows.config import APP_DISPLAY_NAME, TITLE_BAR_HEIGHT


class TitleBar(QWidget):
    """Drag-полоса с названием приложения слева."""

    def __init__(
        self,
        window: QWidget,
        parent: Optional[QWidget] = None,
        *,
        title: str = APP_DISPLAY_NAME,
        font: Optional[QFont] = None,
    ) -> None:
        super().__init__(parent)
        self._window = window
        self._drag_origin = None

        self.setObjectName("titleBar")
        self.setFixedHeight(TITLE_BAR_HEIGHT)

        self._title_label = QLabel(title, self)
        self._title_label.setObjectName("appTitle")
        if font is not None:
            title_font = QFont(font)
            title_font.setPixelSize(11)
            title_font.setBold(True)
            self._title_label.setFont(title_font)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._title_label)
        layout.addStretch(1)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_origin = (
                event.globalPosition().toPoint() - self._window.frameGeometry().topLeft()
            )
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if (
            event.buttons() == Qt.MouseButton.LeftButton
            and self._drag_origin is not None
        ):
            self._window.move(event.globalPosition().toPoint() - self._drag_origin)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._drag_origin = None
        super().mouseReleaseEvent(event)
