"""Логика перевода через Google Translate (с запасным MyMemory)."""

from __future__ import annotations

import re
from typing import Optional

import requests
from PyQt6.QtCore import QObject, pyqtSignal
from bs4 import BeautifulSoup
from deep_translator import MyMemoryTranslator
from deep_translator.exceptions import TranslationNotFound

from translate_meows.config import (
    GOOGLE_TRANSLATE_GTX_URL,
    GOOGLE_TRANSLATE_HEADERS,
    GOOGLE_TRANSLATE_MOBILE_URL,
    MAX_TRANSLATE_CHARS,
    MYMEMORY_LANG,
    TRANSLATE_TIMEOUT_S,
)

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
    if isinstance(exc, TranslationNotFound) or "no translation was found" in message:
        return "Сервис перевода не ответил. Попробуйте ещё раз через несколько секунд."
    if "too many requests" in message or "429" in message:
        return "Слишком много запросов к переводчику. Подождите немного и повторите."
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
    return "Не удалось перевести текст. Попробуйте ещё раз."


def _looks_like_error_page(text: str) -> bool:
    lowered = text.lower()
    return "error 500" in lowered or "that's an error" in lowered or "thats an error" in lowered


def _translate_google_mobile(text: str, source: str, target: str) -> str:
    response = requests.get(
        GOOGLE_TRANSLATE_MOBILE_URL,
        params={"sl": source, "tl": target, "q": text},
        headers=GOOGLE_TRANSLATE_HEADERS,
        timeout=TRANSLATE_TIMEOUT_S,
    )
    if response.status_code == 429:
        raise TranslationNotFound("too many requests")
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    element = soup.find("div", class_="result-container")
    if element is None:
        raise TranslationNotFound(text)

    translated = element.get_text(strip=True)
    if not translated or _looks_like_error_page(translated):
        raise TranslationNotFound(text)
    return translated


def _translate_google_gtx(text: str, source: str, target: str) -> str:
    response = requests.get(
        GOOGLE_TRANSLATE_GTX_URL,
        params={"client": "gtx", "sl": source, "tl": target, "dt": "t", "q": text},
        headers=GOOGLE_TRANSLATE_HEADERS,
        timeout=TRANSLATE_TIMEOUT_S,
    )
    if response.status_code == 429:
        raise TranslationNotFound("too many requests")
    response.raise_for_status()

    payload = response.json()
    chunks = payload[0] if payload else None
    if not chunks:
        raise TranslationNotFound(text)

    translated = "".join(part[0] for part in chunks if part and part[0])
    if not translated or _looks_like_error_page(translated):
        raise TranslationNotFound(text)
    return translated


def _translate_mymemory(text: str, source: str, target: str) -> str:
    translated = MyMemoryTranslator(
        source=MYMEMORY_LANG.get(source, source),
        target=MYMEMORY_LANG.get(target, target),
    ).translate(text)
    if not translated or _looks_like_error_page(translated):
        raise TranslationNotFound(text)
    return translated


def translate_text(text: str, source: str, target: str) -> str:
    """Переводит текст; при сбое Google пробует запасной движок."""
    if len(text) > MAX_TRANSLATE_CHARS:
        raise ValueError("Текст слишком длинный для перевода.")

    last_error: Exception | None = None
    for translator in (
        _translate_google_mobile,
        _translate_google_gtx,
        _translate_mymemory,
    ):
        try:
            return translator(text, source, target)
        except Exception as exc:
            last_error = exc

    raise last_error or TranslationNotFound(text)


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
            translated = translate_text(text, resolved_source, resolved_target)
            self.finished.emit(translated or "", request_id)
        except Exception as exc:
            self.error.emit(friendly_error(exc), request_id)
