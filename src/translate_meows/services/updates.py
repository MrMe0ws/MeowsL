"""Проверка новой версии через GitHub Releases."""

from __future__ import annotations

import re
from dataclasses import dataclass

import requests
from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal

from translate_meows.config import APP_VERSION, GITHUB_LATEST_API, UPDATE_TIMEOUT_S

_VERSION_RE = re.compile(r"(\d+(?:\.\d+)*)")


@dataclass(frozen=True)
class UpdateResult:
    """Итог проверки: есть ли новая версия и что показать пользователю."""

    available: bool
    latest: str
    message: str
    ok: bool


def _as_tuple(version: str) -> tuple[int, ...]:
    match = _VERSION_RE.search(version or "")
    if not match:
        return ()
    return tuple(int(part) for part in match.group(1).split("."))


def is_newer(latest: str, current: str = APP_VERSION) -> bool:
    latest_parts = _as_tuple(latest)
    current_parts = _as_tuple(current)
    if not latest_parts or not current_parts:
        return False
    length = max(len(latest_parts), len(current_parts))
    latest_parts += (0,) * (length - len(latest_parts))
    current_parts += (0,) * (length - len(current_parts))
    return latest_parts > current_parts


class _UpdateProbe(QRunnable):
    def __init__(self, signals: "UpdateSignals") -> None:
        super().__init__()
        self._signals = signals

    def run(self) -> None:
        try:
            response = requests.get(
                GITHUB_LATEST_API,
                headers={"Accept": "application/vnd.github+json"},
                timeout=UPDATE_TIMEOUT_S,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception:
            self._signals.done.emit(
                UpdateResult(False, "", "Не удалось связаться с GitHub", False)
            )
            return

        tag = str(payload.get("tag_name") or payload.get("name") or "").strip()
        latest = tag.lstrip("vV")
        if not latest:
            self._signals.done.emit(
                UpdateResult(False, "", "GitHub не вернул номер версии", False)
            )
            return

        if is_newer(latest):
            self._signals.done.emit(
                UpdateResult(True, latest, f"Доступна версия {latest}", True)
            )
            return

        self._signals.done.emit(
            UpdateResult(False, latest, "Установлена последняя версия", True)
        )


class UpdateSignals(QObject):
    done = pyqtSignal(object)


def check(parent: QObject) -> UpdateSignals:
    """Запускает проверку в фоне и возвращает сигнал с UpdateResult."""
    signals = UpdateSignals(parent)
    QThreadPool.globalInstance().start(_UpdateProbe(signals))
    return signals
