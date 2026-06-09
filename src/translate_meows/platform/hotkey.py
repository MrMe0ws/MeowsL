"""Глобальные хоткеи через библиотеку keyboard."""

import time
from threading import Lock
from typing import Callable, Optional

import keyboard

from translate_meows.config import (
    DOUBLE_CTRL_C_INTERVAL_MS,
    FALLBACK_HOTKEY,
    SCREEN_CAPTURE_SCAN_CODE,
)


def _register_scan_code_hotkey(
    scan_code: int,
    callback: Callable[[], None],
    *,
    suppress: bool = True,
) -> Callable[[], None]:
    """
    Привязка к физической клавише по scan code.
    Нужна для клавиши Ё, т.к. имя символа зависит от раскладки.
    """
    from keyboard import KEY_DOWN, _listener as listener

    def hook(event) -> bool:
        if event.event_type == KEY_DOWN:
            callback()
        if suppress:
            return False
        return True

    listener.start_if_necessary()
    store = listener.blocking_keys if suppress else listener.nonblocking_keys
    store[scan_code].append(hook)

    def remove() -> None:
        if hook in store[scan_code]:
            store[scan_code].remove(hook)

    return remove


class HotkeyListener:
    """
    Слушает глобальные хоткеи:
    - Ctrl+C+C (двойное нажатие за 500 мс) — перевод из буфера
    - Ctrl+Alt+T — запасной
    - Ё (физ. клавиша scan 41) — выделение области экрана
    """

    def __init__(
        self,
        on_trigger: Callable[[], None],
        on_screen_capture: Callable[[], None],
    ) -> None:
        self._on_trigger = on_trigger
        self._on_screen_capture = on_screen_capture
        self._last_ctrl_c = 0.0
        self._interval = DOUBLE_CTRL_C_INTERVAL_MS / 1000.0
        self._lock = Lock()
        self._ctrl_c_handle = None
        self._fallback_handle = None
        self._screen_capture_remove: Optional[Callable[[], None]] = None

    def start(self) -> None:
        self._ctrl_c_handle = keyboard.add_hotkey(
            "ctrl+c", self._on_ctrl_c, suppress=False, trigger_on_release=False
        )
        self._fallback_handle = keyboard.add_hotkey(
            FALLBACK_HOTKEY, self._on_trigger, suppress=False
        )
        self._screen_capture_remove = _register_scan_code_hotkey(
            SCREEN_CAPTURE_SCAN_CODE,
            self._on_screen_capture,
            suppress=True,
        )

    def stop(self) -> None:
        if self._ctrl_c_handle is not None:
            keyboard.remove_hotkey(self._ctrl_c_handle)
            self._ctrl_c_handle = None
        if self._fallback_handle is not None:
            keyboard.remove_hotkey(self._fallback_handle)
            self._fallback_handle = None
        if self._screen_capture_remove is not None:
            self._screen_capture_remove()
            self._screen_capture_remove = None

    def _on_ctrl_c(self) -> None:
        now = time.monotonic()
        with self._lock:
            if self._last_ctrl_c and (now - self._last_ctrl_c) <= self._interval:
                self._last_ctrl_c = 0.0
                self._on_trigger()
            else:
                self._last_ctrl_c = now
