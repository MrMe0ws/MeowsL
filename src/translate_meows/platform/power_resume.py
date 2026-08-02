"""Переподключение хоткеев после выхода Windows из сна / разблокировки сессии."""

from __future__ import annotations

import ctypes
import sys
import time
from ctypes import Structure, wintypes
from typing import Callable

from PyQt6.QtCore import QAbstractNativeEventFilter, QByteArray, Qt, QTimer
from PyQt6.QtWidgets import QApplication, QWidget

from translate_meows.config import HOTKEY_RESUME_DEBOUNCE_S, HOTKEY_RESUME_DELAY_MS

WM_POWERBROADCAST = 0x218
WM_WTSSESSION_CHANGE = 0x2B1
PBT_APMRESUMECRITICAL = 0x6
PBT_APMRESUMESUSPEND = 0x7
PBT_APMRESUMEAUTOMATIC = 0x12
WTS_SESSION_UNLOCK = 0x8
NOTIFY_FOR_THIS_SESSION = 0
DEVICE_NOTIFY_WINDOW_HANDLE = 0

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


def _is_resume_message(message: int, wparam: int) -> bool:
    if message == WM_POWERBROADCAST and wparam in _RESUME_EVENTS:
        return True
    if message == WM_WTSSESSION_CHANGE and wparam == WTS_SESSION_UNLOCK:
        return True
    return False


class _ResumeScheduler:
    """Debounce + отложенный вызов on_resume из главного потока Qt."""

    def __init__(self, on_resume: Callable[[], None]) -> None:
        self._on_resume = on_resume
        self._last_resume_at = 0.0

    def schedule(self) -> None:
        now = time.monotonic()
        if now - self._last_resume_at < HOTKEY_RESUME_DEBOUNCE_S:
            return
        self._last_resume_at = now
        QTimer.singleShot(HOTKEY_RESUME_DELAY_MS, self._on_resume)


class PowerResumeWindow(QWidget):
    """Скрытое top-level окно: гарантированно получает WM_POWERBROADCAST."""

    def __init__(self, scheduler: _ResumeScheduler) -> None:
        super().__init__()
        self._scheduler = scheduler
        self._session_registered = False
        self._suspend_notify = None

        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
            | Qt.WindowType.WindowStaysOnBottomHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
        self.resize(1, 1)
        # Нужен HWND, иначе power/session уведомления не придут.
        self.show()
        self.hide()
        self._register_notifications()

    def _register_notifications(self) -> None:
        try:
            hwnd = int(self.winId())
        except (TypeError, ValueError):
            return

        try:
            ctypes.windll.wtsapi32.WTSRegisterSessionNotification(
                wintypes.HWND(hwnd), NOTIFY_FOR_THIS_SESSION
            )
            self._session_registered = True
        except Exception:
            self._session_registered = False

        try:
            # Windows 8+: явная подписка на suspend/resume.
            handle = ctypes.windll.user32.RegisterSuspendResumeNotification(
                wintypes.HANDLE(hwnd), DEVICE_NOTIFY_WINDOW_HANDLE
            )
            self._suspend_notify = handle or None
        except Exception:
            self._suspend_notify = None

    def nativeEvent(self, eventType, message):  # noqa: N802 — Qt API
        # Не вызываем super().nativeEvent() — на Windows/PyQt6 это нестабильно.
        if bytes(eventType) != b"windows_generic_MSG":
            return False, 0

        try:
            msg = _MSG.from_address(int(message))
        except (TypeError, ValueError, OverflowError):
            return False, 0

        if _is_resume_message(msg.message, int(msg.wParam)):
            self._scheduler.schedule()
        return False, 0

    def cleanup(self) -> None:
        try:
            hwnd = int(self.winId())
        except (TypeError, ValueError):
            hwnd = 0

        if self._session_registered and hwnd:
            try:
                ctypes.windll.wtsapi32.WTSUnRegisterSessionNotification(
                    wintypes.HWND(hwnd)
                )
            except Exception:
                pass
            self._session_registered = False

        if self._suspend_notify:
            try:
                ctypes.windll.user32.UnregisterSuspendResumeNotification(
                    self._suspend_notify
                )
            except Exception:
                pass
            self._suspend_notify = None


class PowerResumeFilter(QAbstractNativeEventFilter):
    """Запасной фильтр на уровне QApplication."""

    def __init__(self, scheduler: _ResumeScheduler) -> None:
        super().__init__()
        self._scheduler = scheduler

    def nativeEventFilter(self, eventType, message) -> tuple[bool, int]:
        if eventType != _WINDOWS_MSG:
            return False, 0

        try:
            msg = _MSG.from_address(int(message))
        except (TypeError, ValueError, OverflowError):
            return False, 0

        if _is_resume_message(msg.message, int(msg.wParam)):
            self._scheduler.schedule()
        return False, 0


class PowerResumeWatcher:
    """Скрытое окно + фильтр приложений для событий пробуждения."""

    def __init__(self, app: QApplication, on_resume: Callable[[], None]) -> None:
        self._scheduler = _ResumeScheduler(on_resume)
        self._window = PowerResumeWindow(self._scheduler)
        self._filter = PowerResumeFilter(self._scheduler)
        app.installNativeEventFilter(self._filter)
        self._app = app

    def cleanup(self) -> None:
        self._app.removeNativeEventFilter(self._filter)
        self._window.cleanup()
        self._window.close()
        self._window.deleteLater()


def install_power_resume_handler(
    app: QApplication,
    on_resume: Callable[[], None],
) -> PowerResumeWatcher | None:
    """Устанавливает обработчики пробуждения Windows. Только win32."""
    if sys.platform != "win32":
        return None
    return PowerResumeWatcher(app, on_resume)
