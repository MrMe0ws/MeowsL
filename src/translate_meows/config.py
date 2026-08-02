"""Константы и настройки приложения."""

APP_NAME = "Translate Meows"
APP_DISPLAY_NAME = "MeowsL"
APP_VERSION = "0.3.2"

# Перевод
DEBOUNCE_MS = 600
MAX_DETECT_LENGTH = 500

# Глобальные хоткеи
DOUBLE_CTRL_C_INTERVAL_MS = 500
FALLBACK_HOTKEY = "ctrl+alt+t"
HOTKEY_RESUME_DELAY_MS = 500
HOTKEY_RESUME_DEBOUNCE_S = 2.0
# Физическая клавиша слева от «1» (Ё / `) — scan code 41 на стандартной раскладке
SCREEN_CAPTURE_SCAN_CODE = 41

# Захват области экрана
MIN_SELECTION_SIZE = 10
POPUP_ANCHOR_MARGIN = 12

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
SETTINGS_KEY_AUTOSTART = "autostart/enabled"
SETTINGS_GEOMETRY_SAVE_MS = 300
FIELD_PADDING = 14

# Языковые метки в полях
LANG_DISPLAY = {
    "en": "ENGLISH",
    "ru": "RUSSIAN",
}
