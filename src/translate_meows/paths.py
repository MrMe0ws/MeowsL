"""Пути к ресурсам проекта (работает и в .exe через PyInstaller)."""

import os
import sys
from pathlib import Path

from translate_meows.config import APP_DISPLAY_NAME, SETTINGS_ORG


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[2]


def asset_path(*parts: str) -> Path:
    return project_root().joinpath(*parts)


def user_data_dir() -> Path:
    r"""%LOCALAPPDATA%\MeowsLate\MeowsL — история и прочие данные пользователя."""
    local = os.environ.get("LOCALAPPDATA")
    base = Path(local) if local else Path.home() / "AppData" / "Local"
    path = base / SETTINGS_ORG / APP_DISPLAY_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path
