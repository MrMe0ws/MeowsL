"""Текстовое поле: языковая метка + иконка копирования по hover."""

from typing import Callable, Optional

from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6.QtGui import QColor, QFont, QTextCharFormat
from PyQt6.QtWidgets import (
    QGraphicsOpacityEffect,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

_TEXT_COLOR = "#f2f2f4"


class PlainTextEdit(QTextEdit):
    """QTextEdit без rich text из буфера — только plain text с цветом темы."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(_TEXT_COLOR))
        self.setCurrentCharFormat(fmt)

    def insertFromMimeData(self, source) -> None:
        if source is not None and source.hasText():
            self.insertPlainText(source.text())


class TextPanel(QWidget):
    """Монолитный блок: метка языка сверху слева, копирование снизу справа."""

    _SELECTABLE = (
        Qt.TextInteractionFlag.TextSelectableByMouse
        | Qt.TextInteractionFlag.TextSelectableByKeyboard
    )

    def __init__(
        self,
        object_name: str,
        placeholder: str,
        font: QFont,
        lang_label: str,
        *,
        editable: bool = True,
        on_copy: Optional[Callable[[], None]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._on_copy_callback = on_copy
        self.setObjectName("textPanel")
        self.setMouseTracking(True)

        self._lang_badge = QLabel(lang_label, self)
        self._lang_badge.setObjectName("langBadge")
        badge_font = QFont(font)
        badge_font.setPixelSize(10)
        self._lang_badge.setFont(badge_font)

        EditorClass = PlainTextEdit if editable else QTextEdit
        self.editor = EditorClass(self)
        self.editor.setObjectName(object_name)
        self.editor.setPlaceholderText(placeholder)
        self.editor.setFont(font)
        self.editor.setFrameShape(QTextEdit.Shape.NoFrame)
        self.editor.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.editor.setMouseTracking(True)

        if editable:
            self.editor.setTextInteractionFlags(
                self._SELECTABLE | Qt.TextInteractionFlag.TextEditable
            )
        else:
            self.editor.setReadOnly(True)
            self.editor.setTextInteractionFlags(self._SELECTABLE)

        self._copy_btn = QPushButton("⧉", self)
        self._copy_btn.setObjectName("copyIcon")
        self._copy_btn.setFixedSize(22, 22)
        self._copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._copy_btn.setToolTip("Копировать")
        self._copy_btn.clicked.connect(self._copy)

        self._copy_opacity = QGraphicsOpacityEffect(self._copy_btn)
        self._copy_opacity.setOpacity(0.0)
        self._copy_btn.setGraphicsEffect(self._copy_opacity)
        self._copy_btn.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.editor)

        self.editor.installEventFilter(self)
        self._position_overlays()

    def set_lang_label(self, text: str) -> None:
        self._lang_badge.setText(text.upper())

    def _copy(self) -> None:
        if self._on_copy_callback is not None:
            self._on_copy_callback()

    def _has_text(self) -> bool:
        return bool(self.editor.toPlainText().strip())

    def _set_copy_hover(self, hovered: bool) -> None:
        visible = hovered and self._has_text()
        self._copy_opacity.setOpacity(1.0 if visible else 0.0)
        self._copy_btn.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, not visible
        )

    def _position_overlays(self) -> None:
        self._lang_badge.adjustSize()
        self._lang_badge.move(14, 10)
        margin = 10
        self._copy_btn.move(
            max(0, self.width() - self._copy_btn.width() - margin),
            max(0, self.height() - self._copy_btn.height() - margin),
        )

    def enterEvent(self, event) -> None:
        self._set_copy_hover(True)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        if not self._copy_btn.underMouse():
            self._set_copy_hover(False)
        super().leaveEvent(event)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._position_overlays()

    def eventFilter(self, watched: QObject, event) -> bool:
        if watched is self.editor:
            if event.type() == QEvent.Type.Enter:
                self._set_copy_hover(True)
            elif event.type() == QEvent.Type.Leave:
                if not self.underMouse() and not self._copy_btn.underMouse():
                    self._set_copy_hover(False)
        return super().eventFilter(watched, event)
