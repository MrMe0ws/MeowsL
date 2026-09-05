"""Перезапуск приложения с правами администратора."""

from __future__ import annotations

import ctypes
import sys
from pathlib import Path

_SHELL_EXECUTE_MIN_SUCCESS = 32


def relaunch_as_admin() -> bool:
    """Просит UAC перезапустить процесс. True — запрос принят."""
    if getattr(sys, "frozen", False):
        executable = sys.executable
        params = ""
    else:
        executable = sys.executable
        params = f'"{Path(sys.argv[0]).resolve()}"'

    try:
        result = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", executable, params, None, 1
        )
    except Exception:
        return False
    return int(result) > _SHELL_EXECUTE_MIN_SUCCESS
