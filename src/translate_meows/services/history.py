"""История переводов: локальный JSON рядом с настройками пользователя."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from translate_meows.config import HISTORY_FILE, HISTORY_LIMIT
from translate_meows.paths import user_data_dir


@dataclass(frozen=True)
class HistoryEntry:
    """Одна пара «исходник → перевод»."""

    source: str
    target: str
    source_lang: str
    target_lang: str
    timestamp: float

    @property
    def clock(self) -> str:
        return time.strftime("%H:%M", time.localtime(self.timestamp))

    @property
    def day(self) -> str:
        """Ключ группировки: сегодня / вчера / дата."""
        entry_day = time.strftime("%Y-%m-%d", time.localtime(self.timestamp))
        today = time.strftime("%Y-%m-%d", time.localtime())
        yesterday = time.strftime("%Y-%m-%d", time.localtime(time.time() - 86400))
        if entry_day == today:
            return "Сегодня"
        if entry_day == yesterday:
            return "Вчера"
        return time.strftime("%d.%m.%Y", time.localtime(self.timestamp))


def history_path() -> Path:
    return user_data_dir() / HISTORY_FILE


def load() -> list[HistoryEntry]:
    """Читает историю; повреждённый файл считается пустым."""
    path = history_path()
    if not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(raw, list):
        return []

    entries: list[HistoryEntry] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            entries.append(
                HistoryEntry(
                    source=str(item["source"]),
                    target=str(item["target"]),
                    source_lang=str(item.get("source_lang", "")),
                    target_lang=str(item.get("target_lang", "")),
                    timestamp=float(item.get("timestamp", 0.0)),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    return entries[:HISTORY_LIMIT]


def _save(entries: Iterable[HistoryEntry]) -> None:
    payload = [asdict(entry) for entry in entries]
    try:
        history_path().write_text(
            json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8"
        )
    except OSError:
        pass


def add(
    source: str, target: str, source_lang: str, target_lang: str
) -> list[HistoryEntry]:
    """Добавляет запись в начало и возвращает обновлённый список."""
    source = source.strip()
    target = target.strip()
    if not source or not target:
        return load()

    entries = [
        entry
        for entry in load()
        if not (entry.source == source and entry.target == target)
    ]
    entries.insert(
        0,
        HistoryEntry(
            source=source,
            target=target,
            source_lang=source_lang,
            target_lang=target_lang,
            timestamp=time.time(),
        ),
    )
    entries = entries[:HISTORY_LIMIT]
    _save(entries)
    return entries


def clear() -> None:
    try:
        history_path().unlink(missing_ok=True)
    except OSError:
        pass


def group_by_day(entries: Iterable[HistoryEntry]) -> list[tuple[str, list[HistoryEntry]]]:
    """Группирует записи по дню, сохраняя порядок «новые сверху»."""
    groups: list[tuple[str, list[HistoryEntry]]] = []
    for entry in entries:
        label = entry.day
        if groups and groups[-1][0] == label:
            groups[-1][1].append(entry)
        else:
            groups.append((label, [entry]))
    return groups
