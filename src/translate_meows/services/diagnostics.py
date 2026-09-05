"""Проверки окружения для вкладок «Состояние» и «Диагностика»."""

from __future__ import annotations

import platform
import sys
from dataclasses import dataclass

import requests
from PyQt6.QtCore import QT_VERSION_STR, QObject, QRunnable, QThreadPool, pyqtSignal

from translate_meows.config import (
    GOOGLE_TRANSLATE_HEADERS,
    GOOGLE_TRANSLATE_MOBILE_URL,
    TRANSLATE_TIMEOUT_S,
)

OCR_LANGS = ("ru", "en")
OCR_LANG_NAMES = {"ru": "русский", "en": "английский"}


@dataclass(frozen=True)
class Check:
    """Результат одной проверки: заголовок, подпись и состояние."""

    title: str
    detail: str
    ok: bool


def ocr_languages() -> list[str]:
    """Коды языков Windows OCR, доступных в системе."""
    try:
        from winrt.windows.globalization import Language
        from winrt.windows.media.ocr import OcrEngine
    except Exception:
        return []

    available: list[str] = []
    for code in OCR_LANGS:
        try:
            if OcrEngine.is_language_supported(Language(code)):
                available.append(code)
        except Exception:
            continue
    return available


def ocr_check() -> Check:
    langs = ocr_languages()
    if not langs:
        return Check(
            "Языковые пакеты OCR",
            "Не найдены — перевод с экрана работать не будет",
            False,
        )
    names = ", ".join(OCR_LANG_NAMES.get(code, code) for code in langs)
    return Check("Языковые пакеты OCR", f"Windows OCR: {names}", True)


def is_elevated() -> bool:
    """Запущен ли процесс с правами администратора."""
    try:
        import ctypes

        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def runtime_check() -> Check:
    return Check(
        "Python",
        f"{platform.python_version()} · PyQt6 {QT_VERSION_STR}",
        True,
    )


def build_check() -> Check:
    kind = "собранный .exe" if getattr(sys, "frozen", False) else "запуск из исходников"
    return Check("Сборка", f"{kind} · Windows {platform.release()}", True)


class TranslatorProbe(QRunnable):
    """Разовая проверка доступности переводчика в пуле потоков."""

    def __init__(self, signals: "ProbeSignals") -> None:
        super().__init__()
        self._signals = signals

    def run(self) -> None:
        import time

        started = time.monotonic()
        try:
            response = requests.get(
                GOOGLE_TRANSLATE_MOBILE_URL,
                params={"sl": "en", "tl": "ru", "q": "ping"},
                headers=GOOGLE_TRANSLATE_HEADERS,
                timeout=TRANSLATE_TIMEOUT_S,
            )
            response.raise_for_status()
        except Exception:
            self._signals.done.emit(
                Check("Переводчик", "translate.google.com недоступен", False)
            )
            return

        elapsed = int((time.monotonic() - started) * 1000)
        self._signals.done.emit(
            Check("Переводчик", f"translate.google.com · отклик {elapsed} мс", True)
        )


class ProbeSignals(QObject):
    done = pyqtSignal(object)


def probe_translator(parent: QObject) -> ProbeSignals:
    """Запускает сетевую проверку и возвращает сигнал с результатом."""
    signals = ProbeSignals(parent)
    QThreadPool.globalInstance().start(TranslatorProbe(signals))
    return signals
