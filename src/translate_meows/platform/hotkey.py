"""Глобальные хоткеи через библиотеку keyboard."""

import time
from threading import Lock
from typing import Callable, Optional

import keyboard

from translate_meows.config import DOUBLE_CTRL_C_INTERVAL_MS, FALLBACK_HOTKEY


class HotkeyListener:
    """
    Слушает глобальные хоткеи:
    - Ctrl+C+C (двойное нажатие за 500 мс) — основной
    - Ctrl+Alt+T — запасной
    """

    def __init__(self, on_trigger: Callable[[], None]) -> None:
        self._on_trigger = on_trigger
        self._last_ctrl_c = 0.0
        self._interval = DOUBLE_CTRL_C_INTERVAL_MS / 1000.0
        self._lock = Lock()
        self._ctrl_c_handle = None
        self._fallback_handle = None

    def start(self) -> None:
        # add_hotkey надёжнее raw hook на Windows
        self._ctrl_c_handle = keyboard.add_hotkey(
            "ctrl+c", self._on_ctrl_c, suppress=False, trigger_on_release=False
        )
        self._fallback_handle = keyboard.add_hotkey(
            FALLBACK_HOTKEY, self._on_trigger, suppress=False
        )

    def stop(self) -> None:
        if self._ctrl_c_handle is not None:
            keyboard.remove_hotkey(self._ctrl_c_handle)
            self._ctrl_c_handle = None
        if self._fallback_handle is not None:
            keyboard.remove_hotkey(self._fallback_handle)
            self._fallback_handle = None

    def _on_ctrl_c(self) -> None:
        now = time.monotonic()
        with self._lock:
            if self._last_ctrl_c and (now - self._last_ctrl_c) <= self._interval:
                self._last_ctrl_c = 0.0
                self._on_trigger()
            else:
                self._last_ctrl_c = now
