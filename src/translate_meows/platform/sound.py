"""Короткий системный сигнал после распознавания текста."""

from __future__ import annotations

import winsound


def play_notification() -> None:
    """Системный звук «Default Beep». QApplication.beep() часто беззвучен."""
    try:
        winsound.MessageBeep(winsound.MB_OK)
    except Exception:
        pass
