"""Строительные блоки главного окна: клавиши, пилюли статуса, строки списков."""

from typing import Optional, Sequence

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontMetrics
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class ElidedLabel(QLabel):
    """QLabel, который дорисовывает многоточие вместо обрезки по краю."""

    def __init__(self, text: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._full_text = text
        self.setText(text)
        self.setMinimumWidth(40)

    def setFullText(self, text: str) -> None:
        self._full_text = text
        self._apply_elide()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_elide()

    def _apply_elide(self) -> None:
        metrics = QFontMetrics(self.font())
        self.setText(
            metrics.elidedText(
                self._full_text, Qt.TextElideMode.ElideRight, max(0, self.width())
            )
        )


class KeyCombo(QWidget):
    """Комбинация клавиш плашками: Ctrl + C + C."""

    def __init__(
        self, keys: Sequence[str], parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)
        self._layout.addStretch(0)
        self.set_keys(keys)

    def set_keys(self, keys: Sequence[str]) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for index, key in enumerate(keys):
            if index:
                plus = QLabel("+", self)
                plus.setObjectName("keyPlus")
                plus.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
                self._layout.addWidget(plus, 0, Qt.AlignmentFlag.AlignVCenter)
            cap = QLabel(key, self)
            cap.setObjectName("keycap")
            cap.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cap.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            self._layout.addWidget(cap, 0, Qt.AlignmentFlag.AlignVCenter)
        self._layout.addStretch(1)


class StatusPill(QLabel):
    """Короткая метка состояния: активен / занят / ошибка."""

    def __init__(self, text: str, tone: str = "ok", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.setObjectName("pill")
        self.setProperty("tone", tone)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_state(self, text: str, tone: str) -> None:
        self.setText(text)
        self.setProperty("tone", tone)
        style = self.style()
        if style is not None:
            style.unpolish(self)
            style.polish(self)


class SectionLabel(QLabel):
    """Заголовок группы: мелкие прописные с трекингом."""

    def __init__(self, text: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(text.upper(), parent)
        self.setObjectName("sectionLabel")
        font = QFont(self.font())
        font.setPixelSize(10)
        font.setBold(True)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.4)
        self.setFont(font)


class Row(QWidget):
    """Строка списка: слева заголовок с подписью, справа управление."""

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        *,
        leading: Optional[QWidget] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("row")

        self._title = QLabel(title, self)
        self._title.setObjectName("rowTitle")
        self._subtitle = QLabel(subtitle, self)
        self._subtitle.setObjectName("rowSubtitle")
        self._subtitle.setWordWrap(True)
        self._subtitle.setVisible(bool(subtitle))

        text = QVBoxLayout()
        text.setContentsMargins(0, 0, 0, 0)
        text.setSpacing(1)
        text.addWidget(self._title)
        text.addWidget(self._subtitle)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 11, 0, 11)
        self._layout.setSpacing(14)
        if leading is not None:
            self._layout.addWidget(leading, 0, Qt.AlignmentFlag.AlignVCenter)
        self._layout.addLayout(text, 1)

    def add_control(self, widget: QWidget) -> QWidget:
        self._layout.addWidget(widget, 0, Qt.AlignmentFlag.AlignVCenter)
        return widget

    def set_subtitle(self, text: str) -> None:
        self._subtitle.setText(text)
        self._subtitle.setVisible(bool(text))

    def set_title(self, text: str) -> None:
        self._title.setText(text)


class Divider(QWidget):
    """Разделитель в 1 px между строками списка."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("divider")
        self.setFixedHeight(1)


def small_button(text: str, tooltip: str = "") -> QPushButton:
    """Компактная кнопка-действие справа в строке."""
    button = QPushButton(text)
    button.setObjectName("miniBtn")
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    if tooltip:
        button.setToolTip(tooltip)
    return button


class RowList(QWidget):
    """Вертикальный список строк с разделителями."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._rows: list[QWidget] = []

    def add(self, widget: QWidget) -> QWidget:
        if self._rows:
            self._layout.addWidget(Divider(self))
        self._layout.addWidget(widget)
        self._rows.append(widget)
        return widget

    def clear(self) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        self._rows.clear()

    def is_empty(self) -> bool:
        return not self._rows
