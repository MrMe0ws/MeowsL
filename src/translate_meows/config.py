"""Константы и настройки приложения."""

APP_NAME = "Translate Meows"
APP_DISPLAY_NAME = "MeowsL"
APP_VERSION = "0.2.0"

# Перевод
DEBOUNCE_MS = 600
MAX_DETECT_LENGTH = 500

# Глобальные хоткеи
DOUBLE_CTRL_C_INTERVAL_MS = 500
FALLBACK_HOTKEY = "ctrl+alt+t"

# Окно
POPUP_WIDTH = 420
POPUP_HEIGHT = 320
POPUP_MIN_WIDTH = 320
POPUP_MIN_HEIGHT = 220
TITLE_BAR_HEIGHT = 32
WINDOW_MARGIN = 8
BORDER_RADIUS = 12
RESIZE_MARGIN = 10

# QSettings
SETTINGS_ORG = "MeowsLate"
SETTINGS_APP = "TranslateMeows"
SETTINGS_KEY_POPUP_GEOMETRY = "popup/geometry"
SETTINGS_GEOMETRY_SAVE_MS = 300
FIELD_PADDING = 14

# Языковые метки в полях
LANG_DISPLAY = {
    "en": "ENGLISH",
    "ru": "RUSSIAN",
}
