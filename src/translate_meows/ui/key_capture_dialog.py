"""Диалог перепривязки клавиши перевода с экрана."""

from typing import Optional

import keyboard
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from translate_meows.config import SCREEN_CAPTURE_LABEL, SCREEN_CAPTURE_SCAN_CODE
from translate_meows.ui.fonts import app_font
from translate_meows.ui.icons import app_icon
from translate_meows.ui.styles import MAIN_WINDOW_STYLESHEET

# Клавиши, которые нельзя назначить: ими закрывают диалог или ломают систему.
_FORBIDDEN_NAMES = {"esc", "enter", "windows", "left windows", "right windows"}


def _pretty(name: str, scan_code: int) -> str:
    """Человеческая подпись клавиши для интерфейса."""
    if not name:
        return f"#{scan_code}"
    if scan_code == SCREEN_CAPTURE_SCAN_CODE:
        return SCREEN_CAPTURE_LABEL
    if len(name) == 1:
        return name.upper()
    return name.capitalize()


class KeyCaptureDialog(QDialog):
    """Ловит одно физическое нажатие и возвращает scan code с подписью."""

    key_captured = pyqtSignal(int, str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._hook = None
        self._scan_code: Optional[int] = None
        self._label: str = ""

        self.setWindowTitle("Клавиша перевода с экрана")
        self.setWindowIcon(app_icon())
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setModal(True)
        self.setFixedSize(360, 210)
        self.setStyleSheet(MAIN_WINDOW_STYLESHEET)
        self.setFont(app_font(10))

        self._build_ui()
        self.key_captured.connect(
            self._on_key_captured, Qt.ConnectionType.QueuedConnection
        )

    def _build_ui(self) -> None:
        container = QWidget(self)
        container.setObjectName("captureDialog")

        title = QLabel("Нажмите клавишу", container)
        title.setObjectName("captureTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._key_label = QLabel("…", container)
        self._key_label.setObjectName("captureKey")
        self._key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._hint = QLabel(
            "Одна клавиша без модификаторов. Esc — отмена.", container
        )
        self._hint.setObjectName("captureHint")
        self._hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hint.setWordWrap(True)

        self._save = QPushButton("Сохранить", container)
        self._save.setObjectName("miniBtn")
        self._save.setEnabled(False)
        self._save.setCursor(Qt.CursorShape.PointingHandCursor)
        self._save.clicked.connect(self.accept)

        reset = QPushButton("По умолчанию", container)
        reset.setObjectName("miniBtn")
        reset.setCursor(Qt.CursorShape.PointingHandCursor)
        reset.clicked.connect(self._on_reset)

        cancel = QPushButton("Отмена", container)
        cancel.setObjectName("miniBtn")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.clicked.connect(self.reject)

        buttons = QHBoxLayout()
        buttons.setContentsMargins(0, 0, 0, 0)
        buttons.setSpacing(8)
        buttons.addWidget(reset)
        buttons.addStretch(1)
        buttons.addWidget(cancel)
        buttons.addWidget(self._save)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(12)
        layout.addWidget(title)
        layout.addWidget(self._key_label, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._hint)
        layout.addStretch(1)
        layout.addLayout(buttons)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(container)

        key_font = QFont(app_font(10))
        key_font.setPixelSize(20)
        key_font.setBold(True)
        self._key_label.setFont(key_font)

    # --- перехват ---------------------------------------------------------

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._start_hook()

    def closeEvent(self, event) -> None:
        self._stop_hook()
        super().closeEvent(event)

    def done(self, result: int) -> None:
        self._stop_hook()
        super().done(result)

    def _start_hook(self) -> None:
        if self._hook is not None:
            return
        try:
            self._hook = keyboard.hook(self._on_keyboard_event, suppress=False)
        except Exception:
            self._hook = None
            self._hint.setText("Не удалось перехватить клавиатуру")

    def _stop_hook(self) -> None:
        if self._hook is None:
            return
        try:
            keyboard.unhook(self._hook)
        except (KeyError, ValueError):
            pass
        self._hook = None

    def _on_keyboard_event(self, event) -> None:
        """Выполняется в потоке keyboard — в Qt уходим через сигнал."""
        if event.event_type != keyboard.KEY_DOWN:
            return
        scan_code = getattr(event, "scan_code", None)
        if not scan_code:
            return
        self.key_captured.emit(int(scan_code), str(event.name or ""))

    def _on_key_captured(self, scan_code: int, name: str) -> None:
        lowered = name.lower()
        if lowered == "esc":
            self.reject()
            return
        if lowered in _FORBIDDEN_NAMES:
            self._hint.setText(f"Клавишу «{name}» назначить нельзя")
            return

        self._scan_code = scan_code
        self._label = _pretty(name, scan_code)
        self._key_label.setText(self._label)
        self._hint.setText(f"scan code {scan_code} — нажмите «Сохранить»")
        self._save.setEnabled(True)

    def _on_reset(self) -> None:
        self._scan_code = SCREEN_CAPTURE_SCAN_CODE
        self._label = SCREEN_CAPTURE_LABEL
        self._key_label.setText(self._label)
        self._hint.setText("Стандартная клавиша слева от «1»")
        self._save.setEnabled(True)

    # --- результат --------------------------------------------------------

    def result_key(self) -> Optional[tuple[int, str]]:
        if self._scan_code is None:
            return None
        return self._scan_code, self._label
