"""Логика перевода через deep_translator."""

import re
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal

from deep_translator import GoogleTranslator

CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")
LATIN_RE = re.compile(r"[a-zA-Z]")


def detect_language(text: str) -> str:
    """Определяет ru/en по доле кириллицы и латиницы (без внешнего API)."""
    cyrillic = len(CYRILLIC_RE.findall(text))
    latin = len(LATIN_RE.findall(text))
    if cyrillic > latin:
        return "ru"
    return "en"


def target_language(detected: str) -> str:
    """Определяет целевой язык: ru → en, en → ru, иначе → ru."""
    if detected == "ru":
        return "en"
    if detected == "en":
        return "ru"
    return "ru"


def resolve_direction(
    text: str,
    source: Optional[str] = None,
    target: Optional[str] = None,
) -> tuple[str, str]:
    """Возвращает пару (source, target) для перевода."""
    if source and target:
        return source, target
    detected = detect_language(text)
    return detected, target_language(detected)


def friendly_error(exc: Exception) -> str:
    """Преобразует исключение в понятное сообщение для пользователя."""
    message = str(exc).lower()
    if any(
        token in message
        for token in (
            "connection",
            "network",
            "timeout",
            "internet",
            "resolve",
            "unreachable",
            "ssl",
            "refused",
        )
    ):
        return "Нет подключения к интернету. Проверьте сеть и попробуйте снова."
    return f"Ошибка перевода: {exc}"


class TranslateWorker(QObject):
    """Воркер перевода, живёт на постоянном QThread."""

    translate_requested = pyqtSignal(str, int, object, object)
    finished = pyqtSignal(str, int)
    error = pyqtSignal(str, int)

    def run(
        self,
        text: str,
        request_id: int,
        source: Optional[str],
        target: Optional[str],
    ) -> None:
        text = text.strip()

        if not text:
            self.finished.emit("", request_id)
            return

        try:
            resolved_source, resolved_target = resolve_direction(text, source, target)
            translated = GoogleTranslator(
                source=resolved_source, target=resolved_target
            ).translate(text)
            self.finished.emit(translated or "", request_id)
        except Exception as exc:
            self.error.emit(friendly_error(exc), request_id)
