"""Константы и настройки приложения."""

APP_NAME = "Translate Meows"
APP_DISPLAY_NAME = "MeowsL"
APP_VERSION = "0.5.0"

# Перевод
DEBOUNCE_MS = 600
MAX_DETECT_LENGTH = 500
MAX_TRANSLATE_CHARS = 5000
TRANSLATE_TIMEOUT_S = 15
GOOGLE_TRANSLATE_MOBILE_URL = "https://translate.google.com/m"
GOOGLE_TRANSLATE_GTX_URL = "https://translate.googleapis.com/translate_a/single"
GOOGLE_TRANSLATE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
MYMEMORY_LANG = {
    "en": "en-GB",
    "ru": "ru-RU",
}

# Глобальные хоткеи
DOUBLE_CTRL_C_INTERVAL_MS = 500
FALLBACK_HOTKEY = "ctrl+alt+t"
HOTKEY_RESUME_DELAY_MS = 500
HOTKEY_RESUME_DEBOUNCE_S = 2.0
# Физическая клавиша слева от «1» (Ё / `) — scan code 41 на стандартной раскладке
SCREEN_CAPTURE_SCAN_CODE = 41
SCREEN_CAPTURE_LABEL = "Ё"

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
# Квадрат захвата угла считаем от видимой плашки (не от прозрачного margin)
RESIZE_CORNER = 20

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

# Главное окно
MAIN_WIDTH = 760
MAIN_HEIGHT = 540
MAIN_MIN_WIDTH = 660
MAIN_MIN_HEIGHT = 460
MAIN_RAIL_WIDTH = 176
MAIN_FOOTER_HEIGHT = 44

# Аргумент командной строки для тихого автозапуска
TRAY_ARG = "--tray"

# Настройки (QSettings)
SETTINGS_KEY_MAIN_GEOMETRY = "main/geometry"
SETTINGS_KEY_SHOW_ON_START = "startup/show_window"
SETTINGS_KEY_HISTORY_ENABLED = "history/enabled"
SETTINGS_KEY_LANG_PAIR = "translate/pair"
SETTINGS_KEY_DEBOUNCE = "translate/debounce_ms"
SETTINGS_KEY_AUTO_TRANSLATE = "translate/auto"
SETTINGS_KEY_OCR_LANG = "ocr/language"
SETTINGS_KEY_OCR_SOUND = "ocr/sound"
SETTINGS_KEY_REMEMBER_GEOMETRY = "popup/remember_geometry"
SETTINGS_KEY_CLOSE_ON_BLUR = "popup/close_on_blur"
SETTINGS_KEY_CAPTURE_SCAN = "hotkey/capture_scan_code"
SETTINGS_KEY_CAPTURE_LABEL = "hotkey/capture_label"

# Языковая пара
LANG_PAIR_AUTO = "auto"
LANG_PAIR_CHOICES = (
    (LANG_PAIR_AUTO, "Русский ⇄ English"),
    ("ru:en", "Русский → English"),
    ("en:ru", "English → Русский"),
)

# Задержка перед переводом
DEBOUNCE_CHOICES = (300, 600, 1000)

# Язык распознавания с экрана
OCR_LANG_AUTO = "auto"
OCR_LANG_CHOICES = (
    ("en", "Английский"),
    ("ru", "Русский"),
    (OCR_LANG_AUTO, "Авто (оба языка)"),
)

# История переводов
HISTORY_LIMIT = 50
HISTORY_FILE = "history.json"
HISTORY_PREVIEW_ROWS = 3

# Проект
GITHUB_URL = "https://github.com/MrMe0ws/MeowsL"
GITHUB_RELEASES_URL = "https://github.com/MrMe0ws/MeowsL/releases"
GITHUB_LATEST_API = "https://api.github.com/repos/MrMe0ws/MeowsL/releases/latest"
UPDATE_TIMEOUT_S = 8
