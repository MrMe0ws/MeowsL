"""Переподключение хоткеев после выхода Windows из сна."""

from __future__ import annotations

import sys
import time
from ctypes import Structure
from ctypes import wintypes
from typing import Callable

from PyQt6.QtCore import QAbstractNativeEventFilter, QByteArray, QTimer
from PyQt6.QtWidgets import QApplication

from translate_meows.config import HOTKEY_RESUME_DEBOUNCE_S, HOTKEY_RESUME_DELAY_MS

WM_POWERBROADCAST = 0x218
PBT_APMRESUMECRITICAL = 0x6
PBT_APMRESUMESUSPEND = 0x7
PBT_APMRESUMEAUTOMATIC = 0x12

_RESUME_EVENTS = frozenset(
    {
        PBT_APMRESUMECRITICAL,
        PBT_APMRESUMESUSPEND,
        PBT_APMRESUMEAUTOMATIC,
    }
)

_WINDOWS_MSG = QByteArray(b"windows_generic_MSG")


class _MSG(Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
    ]


class PowerResumeWatcher(QAbstractNativeEventFilter):
    """Слушает WM_POWERBROADCAST и переподключает хоткеи после пробуждения."""

    def __init__(self, on_resume: Callable[[], None]) -> None:
        super().__init__()
        self._on_resume = on_resume
        self._last_resume_at = 0.0

    def nativeEventFilter(self, eventType, message) -> tuple[bool, int]:
        if eventType != _WINDOWS_MSG:
            return False, 0

        try:
            msg = _MSG.from_address(int(message))
        except (TypeError, ValueError, OverflowError):
            return False, 0

        if msg.message != WM_POWERBROADCAST or msg.wParam not in _RESUME_EVENTS:
            return False, 0

        now = time.monotonic()
        if now - self._last_resume_at < HOTKEY_RESUME_DEBOUNCE_S:
            return False, 0
        self._last_resume_at = now

        QTimer.singleShot(HOTKEY_RESUME_DELAY_MS, self._on_resume)
        return False, 0


def install_power_resume_handler(
    app: QApplication,
    on_resume: Callable[[], None],
) -> PowerResumeWatcher | None:
    """Устанавливает фильтр событий пробуждения Windows. Только win32."""
    if sys.platform != "win32":
        return None

    watcher = PowerResumeWatcher(on_resume)
    app.installNativeEventFilter(watcher)
    return watcher
