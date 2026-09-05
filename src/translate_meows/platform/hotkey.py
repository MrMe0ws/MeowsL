"""Глобальные хоткеи через библиотеку keyboard + Win32 GetAsyncKeyState."""

from __future__ import annotations

import ctypes
import time
from threading import Lock
from typing import Callable, Optional

import keyboard
from keyboard import KEY_DOWN, KEY_UP

from translate_meows import settings as user_settings
from translate_meows.config import DOUBLE_CTRL_C_INTERVAL_MS

_VK_CONTROL = 0x11
_VK_MENU = 0x12  # Alt


def _key_down(vk: int) -> bool:
    """Текущее состояние клавиши из ОС — не зависит от _pressed_events keyboard."""
    return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)


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
    from keyboard import _listener as listener

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


def _register_key_hook(
    scan_codes: tuple[int, ...],
    on_down: Callable[[], None],
    *,
    suppress: bool = False,
) -> Callable[[], None]:
    """Хук на KEY_DOWN по scan codes без auto-repeat (пока клавиша зажата)."""
    from keyboard import _listener as listener

    held: set[int] = set()

    def hook(event) -> bool:
        code = event.scan_code
        if event.event_type == KEY_DOWN:
            if code not in held:
                held.add(code)
                on_down()
        elif event.event_type == KEY_UP:
            held.discard(code)
        if suppress:
            return False
        return True

    listener.start_if_necessary()
    store = listener.blocking_keys if suppress else listener.nonblocking_keys
    for scan_code in scan_codes:
        store[scan_code].append(hook)

    def remove() -> None:
        for scan_code in scan_codes:
            if hook in store[scan_code]:
                store[scan_code].remove(hook)

    return remove


def _reset_keyboard_state() -> None:
    """Сбрасывает залипшее состояние keyboard после сна Windows."""
    listener = keyboard._listener
    with keyboard._pressed_events_lock:
        keyboard._pressed_events.clear()
    keyboard._logically_pressed_keys.clear()
    listener.active_modifiers.clear()
    listener.modifier_states.clear()


class HotkeyListener:
    """
    Слушает глобальные хоткеи:
    - Ctrl+C+C (двойное нажатие за 500 мс) — перевод из буфера
    - Ctrl+Alt+T — запасной
    - Ё (физ. клавиша scan 41) — выделение области экрана

    Ctrl-комбинации проверяют модификаторы через GetAsyncKeyState, а не через
    keyboard.add_hotkey — иначе после сна _pressed_events «залипает» и
    комбинации перестают матчиться, тогда как одиночные scan-code хуки живут.
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
        self._ctrl_c_remove: Optional[Callable[[], None]] = None
        self._fallback_remove: Optional[Callable[[], None]] = None
        self._screen_capture_remove: Optional[Callable[[], None]] = None

    def start(self) -> None:
        c_codes = keyboard.key_to_scan_codes("c")
        t_codes = keyboard.key_to_scan_codes("t")

        self._ctrl_c_remove = _register_key_hook(
            c_codes, self._on_c_down, suppress=False
        )
        self._fallback_remove = _register_key_hook(
            t_codes, self._on_t_down, suppress=False
        )
        self._screen_capture_remove = _register_scan_code_hotkey(
            user_settings.capture_scan_code(),
            self._on_screen_capture,
            suppress=True,
        )

    def stop(self) -> None:
        if self._ctrl_c_remove is not None:
            self._ctrl_c_remove()
            self._ctrl_c_remove = None
        if self._fallback_remove is not None:
            self._fallback_remove()
            self._fallback_remove = None
        if self._screen_capture_remove is not None:
            self._screen_capture_remove()
            self._screen_capture_remove = None

    def restart(self) -> None:
        """Переподключает хоткеи (в т.ч. после смены клавиши) и чистит состояние."""
        self.stop()
        _reset_keyboard_state()
        with self._lock:
            self._last_ctrl_c = 0.0
        self.start()

    def _on_c_down(self) -> None:
        if not _key_down(_VK_CONTROL) or _key_down(_VK_MENU):
            return
        now = time.monotonic()
        with self._lock:
            if self._last_ctrl_c and (now - self._last_ctrl_c) <= self._interval:
                self._last_ctrl_c = 0.0
                self._on_trigger()
            else:
                self._last_ctrl_c = now

    def _on_t_down(self) -> None:
        if _key_down(_VK_CONTROL) and _key_down(_VK_MENU):
            self._on_trigger()
