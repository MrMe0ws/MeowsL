"""Автозапуск с Windows через HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run."""

from __future__ import annotations

import sys
import winreg
from pathlib import Path

from PyQt6.QtCore import QSettings

from translate_meows.config import (
    APP_DISPLAY_NAME,
    SETTINGS_APP,
    SETTINGS_KEY_AUTOSTART,
    SETTINGS_ORG,
)

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _settings() -> QSettings:
    return QSettings(SETTINGS_ORG, SETTINGS_APP)


def launch_command() -> str:
    """Команда для записи в Run."""
    if getattr(sys, "frozen", False):
        return f'"{Path(sys.executable).resolve()}"'
    script = Path(sys.argv[0]).resolve()
    python = Path(sys.executable).resolve()
    return f'"{python}" "{script}"'


def is_enabled_in_registry() -> bool:
    return get_registry_command() is not None


def get_registry_command() -> str | None:
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_READ
        ) as key:
            value, _ = winreg.QueryValueEx(key, APP_DISPLAY_NAME)
    except FileNotFoundError:
        return None
    except OSError:
        return None
    if not value:
        return None
    return str(value)


def is_enabled_in_settings() -> bool:
    return _settings().value(SETTINGS_KEY_AUTOSTART, False, type=bool)


def set_enabled_in_settings(enabled: bool) -> None:
    settings = _settings()
    settings.setValue(SETTINGS_KEY_AUTOSTART, enabled)
    settings.sync()


def _write_registry(command: str | None) -> None:
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        _RUN_KEY,
        0,
        winreg.KEY_SET_VALUE,
    ) as key:
        if command is None:
            try:
                winreg.DeleteValue(key, APP_DISPLAY_NAME)
            except FileNotFoundError:
                pass
        else:
            winreg.SetValueEx(key, APP_DISPLAY_NAME, 0, winreg.REG_SZ, command)


def set_enabled(enabled: bool) -> None:
    """Включает или выключает автозапуск (настройка + реестр)."""
    set_enabled_in_settings(enabled)
    _write_registry(launch_command() if enabled else None)


def sync() -> None:
    """Синхронизирует реестр с настройкой и актуальным путём к exe."""
    desired = is_enabled_in_settings()
    current_cmd = launch_command()
    registry_cmd = get_registry_command()

    if desired:
        if registry_cmd != current_cmd:
            _write_registry(current_cmd)
    elif registry_cmd is not None:
        _write_registry(None)
