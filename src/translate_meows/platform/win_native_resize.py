"""Нативный ресайз frameless-окна через WM_NCHITTEST (Windows).

ВАЖНО: внутри WM_NCHITTEST нельзя вызывать Qt-методы вроде mapFromGlobal —
это приводит к STATUS_FATAL_USER_CALLBACK_EXCEPTION и «тихому» падению процесса.
"""

import sys
from ctypes import POINTER, Structure, c_short, c_void_p, cast
from ctypes import wintypes
from typing import Callable, Optional

from PyQt6.QtCore import QPoint
from PyQt6.QtWidgets import QWidget

WM_NCHITTEST = 0x0084

HTLEFT = 10
HTRIGHT = 11
HTTOP = 12
HTTOPLEFT = 13
HTTOPRIGHT = 14
HTBOTTOM = 15
HTBOTTOMLEFT = 16
HTBOTTOMRIGHT = 17

_EDGE_HT: dict[str, int] = {
    "left": HTLEFT,
    "right": HTRIGHT,
    "top": HTTOP,
    "bottom": HTBOTTOM,
    "top-left": HTTOPLEFT,
    "top-right": HTTOPRIGHT,
    "bottom-left": HTBOTTOMLEFT,
    "bottom-right": HTBOTTOMRIGHT,
}


class MSG(Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
    ]


def is_win_native_resize_available() -> bool:
    # Нативный WM_NCHITTEST отключён: на PyQt6/Python 3.13 даёт нестабильные
    # падения при show(). Ресайз идёт через event filters в FramelessResizeMixin.
    return False


def _msg_pointer(message) -> Optional[int]:
    try:
        address = int(message)
    except (TypeError, ValueError):
        return None
    return address if address > 0 else None


def _screen_point_from_lparam(lparam: int) -> tuple[int, int]:
    x = c_short(lparam & 0xFFFF).value
    y = c_short((lparam >> 16) & 0xFFFF).value
    return x, y


def _local_point(widget: QWidget, screen_x: int, screen_y: int) -> QPoint:
    origin = widget.frameGeometry().topLeft()
    return QPoint(screen_x - origin.x(), screen_y - origin.y())


def handle_win_native_resize(
    widget: QWidget,
    event_type: bytes,
    message: int,
    hit_test: Callable,
) -> Optional[tuple[bool, int]]:
    if not is_win_native_resize_available() or event_type != b"windows_generic_MSG":
        return None

    address = _msg_pointer(message)
    if address is None:
        return None

    msg = cast(c_void_p(address), POINTER(MSG)).contents
    if msg.message != WM_NCHITTEST:
        return None

    screen_x, screen_y = _screen_point_from_lparam(msg.lParam)
    local_pos = _local_point(widget, screen_x, screen_y)
    edge = hit_test(local_pos)
    if edge is None:
        return None

    ht_code = _EDGE_HT.get(edge)
    if ht_code is None:
        return None

    return True, ht_code
