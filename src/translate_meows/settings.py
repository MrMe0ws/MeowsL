"""Типизированный доступ к пользовательским настройкам (QSettings)."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QSettings

from translate_meows.config import (
    DEBOUNCE_MS,
    LANG_PAIR_AUTO,
    SCREEN_CAPTURE_LABEL,
    SCREEN_CAPTURE_SCAN_CODE,
    SETTINGS_APP,
    SETTINGS_KEY_AUTO_TRANSLATE,
    SETTINGS_KEY_CAPTURE_LABEL,
    SETTINGS_KEY_CAPTURE_SCAN,
    SETTINGS_KEY_CLOSE_ON_BLUR,
    SETTINGS_KEY_DEBOUNCE,
    SETTINGS_KEY_HISTORY_ENABLED,
    SETTINGS_KEY_LANG_PAIR,
    SETTINGS_KEY_OCR_LANG,
    SETTINGS_KEY_OCR_SOUND,
    SETTINGS_KEY_REMEMBER_GEOMETRY,
    SETTINGS_KEY_SHOW_ON_START,
    SETTINGS_ORG,
)


def settings() -> QSettings:
    return QSettings(SETTINGS_ORG, SETTINGS_APP)


def _get_bool(key: str, default: bool) -> bool:
    return settings().value(key, default, type=bool)


def _get_int(key: str, default: int) -> int:
    try:
        return int(settings().value(key, default, type=int))
    except (TypeError, ValueError):
        return default


def _get_str(key: str, default: str) -> str:
    value = settings().value(key, default, type=str)
    return value if isinstance(value, str) and value else default


def _set(key: str, value) -> None:
    store = settings()
    store.setValue(key, value)
    store.sync()


def location() -> str:
    """Где физически лежат настройки — для вкладки диагностики."""
    return settings().fileName()


# --- Запуск -----------------------------------------------------------------

def show_window_on_start() -> bool:
    return _get_bool(SETTINGS_KEY_SHOW_ON_START, False)


def set_show_window_on_start(value: bool) -> None:
    _set(SETTINGS_KEY_SHOW_ON_START, value)


# --- Перевод ----------------------------------------------------------------

def lang_pair() -> str:
    return _get_str(SETTINGS_KEY_LANG_PAIR, LANG_PAIR_AUTO)


def set_lang_pair(value: str) -> None:
    _set(SETTINGS_KEY_LANG_PAIR, value)


def forced_direction() -> Optional[tuple[str, str]]:
    """(source, target) при фиксированной паре, иначе None — автоопределение."""
    raw = lang_pair()
    if raw == LANG_PAIR_AUTO or ":" not in raw:
        return None
    source, target = raw.split(":", 1)
    if not source or not target:
        return None
    return source, target


def debounce_ms() -> int:
    return _get_int(SETTINGS_KEY_DEBOUNCE, DEBOUNCE_MS)


def set_debounce_ms(value: int) -> None:
    _set(SETTINGS_KEY_DEBOUNCE, int(value))


def auto_translate() -> bool:
    return _get_bool(SETTINGS_KEY_AUTO_TRANSLATE, True)


def set_auto_translate(value: bool) -> None:
    _set(SETTINGS_KEY_AUTO_TRANSLATE, value)


# --- Перевод с экрана -------------------------------------------------------

def ocr_language() -> str:
    return _get_str(SETTINGS_KEY_OCR_LANG, "en")


def set_ocr_language(value: str) -> None:
    _set(SETTINGS_KEY_OCR_LANG, value)


def ocr_sound() -> bool:
    return _get_bool(SETTINGS_KEY_OCR_SOUND, False)


def set_ocr_sound(value: bool) -> None:
    _set(SETTINGS_KEY_OCR_SOUND, value)


def capture_scan_code() -> int:
    return _get_int(SETTINGS_KEY_CAPTURE_SCAN, SCREEN_CAPTURE_SCAN_CODE)


def capture_label() -> str:
    return _get_str(SETTINGS_KEY_CAPTURE_LABEL, SCREEN_CAPTURE_LABEL)


def set_capture_key(scan_code: int, label: str) -> None:
    """Клавиша перевода с экрана: scan code для хука, подпись для интерфейса."""
    store = settings()
    store.setValue(SETTINGS_KEY_CAPTURE_SCAN, int(scan_code))
    store.setValue(SETTINGS_KEY_CAPTURE_LABEL, label)
    store.sync()


def reset_capture_key() -> None:
    set_capture_key(SCREEN_CAPTURE_SCAN_CODE, SCREEN_CAPTURE_LABEL)


# --- Окно перевода ----------------------------------------------------------

def remember_popup_geometry() -> bool:
    return _get_bool(SETTINGS_KEY_REMEMBER_GEOMETRY, True)


def set_remember_popup_geometry(value: bool) -> None:
    _set(SETTINGS_KEY_REMEMBER_GEOMETRY, value)


def close_popup_on_blur() -> bool:
    return _get_bool(SETTINGS_KEY_CLOSE_ON_BLUR, True)


def set_close_popup_on_blur(value: bool) -> None:
    _set(SETTINGS_KEY_CLOSE_ON_BLUR, value)


# --- История ----------------------------------------------------------------

def history_enabled() -> bool:
    return _get_bool(SETTINGS_KEY_HISTORY_ENABLED, True)


def set_history_enabled(value: bool) -> None:
    _set(SETTINGS_KEY_HISTORY_ENABLED, value)
