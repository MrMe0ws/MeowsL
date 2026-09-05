"""Главное окно: состояние, хоткеи, история, настройки, о программе."""

from typing import Callable, Optional

from PyQt6.QtCore import QByteArray, QEvent, QObject, QTimer, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QColor, QDesktopServices, QFont, QGuiApplication, QPainter
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from translate_meows import settings as user_settings
from translate_meows.config import (
    APP_DISPLAY_NAME,
    APP_VERSION,
    DEBOUNCE_CHOICES,
    FALLBACK_HOTKEY,
    GITHUB_RELEASES_URL,
    GITHUB_URL,
    HISTORY_PREVIEW_ROWS,
    LANG_PAIR_CHOICES,
    MAIN_FOOTER_HEIGHT,
    MAIN_HEIGHT,
    MAIN_MIN_HEIGHT,
    MAIN_MIN_WIDTH,
    MAIN_RAIL_WIDTH,
    MAIN_WIDTH,
    OCR_LANG_CHOICES,
    SETTINGS_GEOMETRY_SAVE_MS,
    SETTINGS_KEY_MAIN_GEOMETRY,
    WINDOW_MARGIN,
)
from translate_meows.platform import autostart
from translate_meows.platform.elevate import relaunch_as_admin
from translate_meows.platform.sound import play_notification
from translate_meows.services import diagnostics, history, updates
from translate_meows.ui.fonts import app_font
from translate_meows.ui.icons import app_icon, logo_pixmap
from translate_meows.ui.key_capture_dialog import KeyCaptureDialog
from translate_meows.ui.styles import MAIN_WINDOW_STYLESHEET
from translate_meows.ui.widgets.combo import ArrowComboBox
from translate_meows.ui.widgets.frameless_resize import FramelessResizeMixin
from translate_meows.ui.widgets.rows import (
    ElidedLabel,
    KeyCombo,
    Row,
    RowList,
    SectionLabel,
    StatusPill,
    small_button,
)
from translate_meows.ui.widgets.switch import Switch
from translate_meows.ui.widgets.title_bar import TitleBar

_TOAST_MS = 2200
_KEY_COLUMN_WIDTH = 142
_TONE_COLORS = {
    "ok": QColor("#5cc48f"),
    "warn": QColor("#d9a441"),
    "idle": QColor("#8e8e93"),
}


class StatusDot(QWidget):
    """Цветная точка состояния с мягким ореолом."""

    def __init__(self, tone: str = "ok", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._tone = tone
        self.setFixedSize(14, 14)

    def set_tone(self, tone: str) -> None:
        self._tone = tone
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = _TONE_COLORS.get(self._tone, _TONE_COLORS["idle"])

        halo = QColor(color)
        halo.setAlpha(46)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(halo)
        painter.drawEllipse(0, 0, 14, 14)

        painter.setBrush(color)
        painter.drawEllipse(3, 3, 8, 8)
        painter.end()


def _one_line(text: str, limit: int = 120) -> str:
    """Схлопывает перевод в одну строку для узкой колонки."""
    flat = " ".join(text.split())
    if len(flat) <= limit:
        return flat
    return flat[: limit - 1] + "…"


class HistoryRow(QWidget):
    """Строка истории: исходник → перевод, копирование по наведению."""

    def __init__(
        self,
        entry: history.HistoryEntry,
        on_open: Callable[[history.HistoryEntry], None],
        on_copy: Callable[[history.HistoryEntry], None],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._entry = entry
        self._on_open = on_open
        self._on_copy = on_copy

        self.setObjectName("historyRow")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setToolTip(f"{entry.source}\n→ {entry.target}")

        source = ElidedLabel(_one_line(entry.source), self)
        source.setObjectName("historySource")
        arrow = QLabel("→", self)
        arrow.setObjectName("historyArrow")
        target = ElidedLabel(_one_line(entry.target), self)
        target.setObjectName("historyTarget")
        for label in (source, target):
            label.setMinimumWidth(60)

        self._copy = QPushButton("⧉", self)
        self._copy.setObjectName("copyBtn")
        self._copy.setCursor(Qt.CursorShape.PointingHandCursor)
        self._copy.setToolTip("Копировать перевод")
        self._copy.setFixedSize(24, 22)
        self._copy.clicked.connect(self._handle_copy)
        self._copy.setVisible(False)

        clock = QLabel(entry.clock, self)
        clock.setObjectName("historyClock")
        clock.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        clock.setFixedWidth(36)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 9, 8, 9)
        layout.setSpacing(10)
        layout.addWidget(source, 1)
        layout.addWidget(arrow, 0)
        layout.addWidget(target, 1)
        layout.addWidget(self._copy, 0)
        layout.addWidget(clock, 0)

    def enterEvent(self, event) -> None:
        self._copy.setVisible(True)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._copy.setVisible(False)
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(
            event.position().toPoint()
        ):
            self._on_open(self._entry)
        super().mouseReleaseEvent(event)

    def _handle_copy(self) -> None:
        self._on_copy(self._entry)


class MainWindow(FramelessResizeMixin, QWidget):
    """Frameless окно приложения с рельсом навигации."""

    translate_clipboard_requested = pyqtSignal()
    screen_capture_requested = pyqtSignal()
    hotkeys_restart_requested = pyqtSignal()
    translate_text_requested = pyqtSignal(str)
    quit_requested = pyqtSignal()

    _PANES = (
        ("home", "Главная"),
        ("keys", "Горячие клавиши"),
        ("history", "История"),
        ("settings", "Настройки"),
        ("about", "О программе"),
    )

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._init_frameless_resize()

        self._font = app_font(10)
        self._pane_index: dict[str, int] = {}
        self._nav_buttons: dict[str, QPushButton] = {}
        self._geometry_restored = False
        self._translator_check: Optional[diagnostics.Check] = None

        self._build_ui()
        self._setup_geometry_persistence()
        if not self.uses_native_resize():
            self._install_resize_event_filters()

    # --- сборка -----------------------------------------------------------

    def _build_ui(self) -> None:
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle(APP_DISPLAY_NAME)
        self.setWindowIcon(app_icon())
        self.setMinimumSize(MAIN_MIN_WIDTH, MAIN_MIN_HEIGHT)
        self.resize(MAIN_WIDTH, MAIN_HEIGHT)
        self.setFont(self._font)

        container = QWidget(self)
        container.setObjectName("mainContainer")
        container.setMouseTracking(True)
        self._container = container

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._build_rail(container), 0)
        body.addWidget(self._build_content(container), 1)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(self._build_header(container))
        layout.addLayout(body, 1)
        layout.addWidget(self._build_footer(container), 0)

        root = QVBoxLayout(self)
        root.setContentsMargins(
            WINDOW_MARGIN, WINDOW_MARGIN, WINDOW_MARGIN, WINDOW_MARGIN
        )
        root.addWidget(container)

        self._toast = QLabel("", container)
        self._toast.setObjectName("toast")
        self._toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._toast.setVisible(False)
        self._toast_timer = QTimer(self)
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(lambda: self._toast.setVisible(False))

        self.setStyleSheet(MAIN_WINDOW_STYLESHEET)
        self._select_pane("home")

    def _build_header(self, parent: QWidget) -> QHBoxLayout:
        title_bar = TitleBar(self, parent, font=self._font)

        minimize = QPushButton("−", parent)
        minimize.setObjectName("headerBtn")
        minimize.setToolTip("Свернуть окно")
        minimize.setCursor(Qt.CursorShape.PointingHandCursor)
        minimize.clicked.connect(self.showMinimized)

        close = QPushButton("×", parent)
        close.setObjectName("closeBtn")
        close.setToolTip("Свернуть в трей — приложение продолжит работать")
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.clicked.connect(self.hide)

        header = QHBoxLayout()
        header.setContentsMargins(8, 4, 6, 0)
        header.setSpacing(2)
        header.addWidget(title_bar, 1)
        header.addWidget(minimize, 0, Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(close, 0, Qt.AlignmentFlag.AlignVCenter)
        return header

    def _build_rail(self, parent: QWidget) -> QWidget:
        rail = QWidget(parent)
        rail.setObjectName("rail")
        rail.setFixedWidth(MAIN_RAIL_WIDTH)
        rail.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        mark = QLabel(rail)
        mark.setPixmap(logo_pixmap(30))
        mark.setFixedSize(30, 30)
        mark.setScaledContents(True)

        name = QLabel(APP_DISPLAY_NAME, rail)
        name.setObjectName("brandName")
        version = QLabel(APP_VERSION, rail)
        version.setObjectName("brandVersion")

        who = QVBoxLayout()
        who.setContentsMargins(0, 0, 0, 0)
        who.setSpacing(0)
        who.addWidget(name)
        who.addWidget(version)

        brand = QHBoxLayout()
        brand.setContentsMargins(6, 6, 6, 16)
        brand.setSpacing(9)
        brand.addWidget(mark, 0, Qt.AlignmentFlag.AlignVCenter)
        brand.addLayout(who, 1)

        nav = QVBoxLayout()
        nav.setContentsMargins(0, 0, 0, 0)
        nav.setSpacing(1)
        for key, label in self._PANES:
            button = QPushButton(label, rail)
            button.setObjectName("navItem")
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _checked, k=key: self._select_pane(k))
            self._nav_buttons[key] = button
            nav.addWidget(button)

        layout = QVBoxLayout(rail)
        layout.setContentsMargins(10, 4, 10, 10)
        layout.setSpacing(0)
        layout.addLayout(brand)
        layout.addLayout(nav)
        layout.addStretch(1)
        return rail

    def _build_content(self, parent: QWidget) -> QWidget:
        self._stack = QStackedWidget(parent)
        self._stack.setObjectName("contentArea")

        for key, builder in (
            ("home", self._build_home_pane),
            ("keys", self._build_keys_pane),
            ("history", self._build_history_pane),
            ("settings", self._build_settings_pane),
            ("about", self._build_about_pane),
        ):
            scroll, body = self._new_pane()
            builder(body)
            body.addStretch(1)
            self._pane_index[key] = self._stack.addWidget(scroll)

        return self._stack

    def _new_pane(self) -> tuple[QScrollArea, QVBoxLayout]:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        page = QWidget()
        page.setObjectName("pane")
        body = QVBoxLayout(page)
        body.setContentsMargins(20, 6, 20, 18)
        body.setSpacing(0)
        scroll.setWidget(page)
        return scroll, body

    def _build_footer(self, parent: QWidget) -> QWidget:
        footer = QWidget(parent)
        footer.setObjectName("mainFooter")
        footer.setFixedHeight(MAIN_FOOTER_HEIGHT)
        footer.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        to_tray = QPushButton("Свернуть в трей", footer)
        to_tray.setObjectName("linkBtn")
        to_tray.setCursor(Qt.CursorShape.PointingHandCursor)
        to_tray.clicked.connect(self.hide)

        version = QLabel(APP_VERSION, footer)
        version.setObjectName("footerVersion")

        check = QPushButton("Проверить обновления", footer)
        check.setObjectName("linkBtn")
        check.setCursor(Qt.CursorShape.PointingHandCursor)
        check.clicked.connect(self._check_updates)

        layout = QHBoxLayout(footer)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(4)
        layout.addWidget(to_tray)
        layout.addStretch(1)
        layout.addWidget(version)
        layout.addWidget(check)
        return footer

    def _section(self, text: str, *, first: bool = False) -> QWidget:
        holder = QWidget()
        layout = QVBoxLayout(holder)
        layout.setContentsMargins(0, 10 if first else 18, 0, 9)
        layout.setSpacing(0)
        layout.addWidget(SectionLabel(text))
        return holder

    # --- вкладка «Главная» ------------------------------------------------

    def _build_home_pane(self, body: QVBoxLayout) -> None:
        body.addWidget(self._section("Состояние", first=True))

        self._status_dot = StatusDot("ok")
        self._status_title = QLabel("Работает в фоне")
        self._status_title.setObjectName("statusTitle")
        self._status_detail = QLabel("Проверяю окружение…")
        self._status_detail.setObjectName("statusDetail")
        self._status_detail.setWordWrap(True)

        status_text = QVBoxLayout()
        status_text.setContentsMargins(0, 0, 0, 0)
        status_text.setSpacing(1)
        status_text.addWidget(self._status_title)
        status_text.addWidget(self._status_detail)

        status = QHBoxLayout()
        status.setContentsMargins(0, 2, 0, 6)
        status.setSpacing(10)
        status.addWidget(self._status_dot, 0, Qt.AlignmentFlag.AlignTop)
        status.addLayout(status_text, 1)
        body.addLayout(status)

        body.addWidget(self._section("Как вызвать перевод"))

        self._capture_card_keys = KeyCombo([user_settings.capture_label()])
        cards = QHBoxLayout()
        cards.setContentsMargins(0, 0, 0, 0)
        cards.setSpacing(10)
        cards.addWidget(
            self._key_card(
                KeyCombo(["Ctrl", "C", "C"]),
                "Перевести текст из буфера обмена",
                self.translate_clipboard_requested.emit,
            ),
            1,
        )
        cards.addWidget(
            self._key_card(
                self._capture_card_keys,
                "Обвести область экрана и распознать текст",
                self.screen_capture_requested.emit,
            ),
            1,
        )
        body.addLayout(cards)

        body.addWidget(self._section("Последние переводы"))
        self._home_history = RowList()
        body.addWidget(self._home_history)

        more = QPushButton("Вся история")
        more.setObjectName("linkBtn")
        more.setCursor(Qt.CursorShape.PointingHandCursor)
        more.clicked.connect(lambda: self._select_pane("history"))
        row = QHBoxLayout()
        row.setContentsMargins(0, 6, 0, 0)
        row.addStretch(1)
        row.addWidget(more)
        body.addLayout(row)

    def _key_card(
        self, keys: KeyCombo, caption: str, on_try: Callable[[], None]
    ) -> QWidget:
        card = QWidget()
        card.setObjectName("keyCard")
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        keys.setParent(card)

        text = QLabel(caption, card)
        text.setObjectName("cardCaption")
        text.setWordWrap(True)

        button = small_button("Попробовать")
        button.clicked.connect(on_try)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.addStretch(1)
        actions.addWidget(button)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 13, 14, 12)
        layout.setSpacing(9)
        layout.addWidget(keys)
        layout.addWidget(text)
        layout.addStretch(1)
        layout.addLayout(actions)
        return card

    # --- вкладка «Горячие клавиши» ---------------------------------------

    def _build_keys_pane(self, body: QVBoxLayout) -> None:
        body.addWidget(self._section("Глобальные хоткеи", first=True))

        hotkeys = RowList()

        clipboard_row = Row(
            "Перевод из буфера",
            "Двойное нажатие Ctrl+C в пределах 500 мс",
            leading=self._key_column(KeyCombo(["Ctrl", "C", "C"])),
        )
        clipboard_row.add_control(StatusPill("активен", "ok"))
        hotkeys.add(clipboard_row)

        self._capture_keys = KeyCombo([user_settings.capture_label()])
        self._capture_row = Row(
            "Перевод с экрана",
            self._capture_subtitle(),
            leading=self._key_column(self._capture_keys),
        )
        self._capture_row.add_control(StatusPill("активен", "ok"))
        rebind = small_button("Изменить", "Назначить другую физическую клавишу")
        rebind.clicked.connect(self._rebind_capture_key)
        self._capture_row.add_control(rebind)
        hotkeys.add(self._capture_row)

        fallback_row = Row(
            "Запасной вызов",
            "Открывает перевод из буфера без двойного нажатия",
            leading=self._key_column(
                KeyCombo([part.capitalize() for part in FALLBACK_HOTKEY.split("+")])
            ),
        )
        fallback_row.add_control(StatusPill("активен", "ok"))
        hotkeys.add(fallback_row)
        body.addWidget(hotkeys)

        body.addWidget(self._section("Если хоткей не срабатывает"))
        repair = RowList()

        admin_row = Row(
            "Запуск от имени администратора",
            "Нужен, когда активное окно запущено с повышенными правами",
        )
        self._admin_button = small_button("Перезапустить")
        self._admin_button.clicked.connect(self._restart_elevated)
        admin_row.add_control(self._admin_button)
        repair.add(admin_row)

        reregister = Row(
            "Перерегистрировать хоткеи",
            "Помогает после выхода из спящего режима",
        )
        run = small_button("Выполнить")
        run.clicked.connect(self._restart_hotkeys)
        reregister.add_control(run)
        repair.add(reregister)

        body.addWidget(repair)

    def _key_column(self, keys: KeyCombo) -> KeyCombo:
        """Общая ширина колонки клавиш — иначе заголовки строк разъезжаются."""
        keys.setFixedWidth(_KEY_COLUMN_WIDTH)
        return keys

    def _capture_subtitle(self) -> str:
        return f"Физическая клавиша, scan code {user_settings.capture_scan_code()}"

    # --- вкладка «История» ------------------------------------------------

    def _build_history_pane(self, body: QVBoxLayout) -> None:
        self._history_groups = QWidget()
        self._history_groups_layout = QVBoxLayout(self._history_groups)
        self._history_groups_layout.setContentsMargins(0, 0, 0, 0)
        self._history_groups_layout.setSpacing(0)
        body.addWidget(self._history_groups)

        body.addWidget(self._section("Хранение"))
        controls = RowList()

        keep_row = Row("Хранить историю", "Последние 50 переводов, локально в файле")
        self._history_switch = Switch(user_settings.history_enabled())
        self._history_switch.toggled_by_user.connect(self._on_history_toggled)
        keep_row.add_control(self._history_switch)
        controls.add(keep_row)

        clear_row = Row("Очистить историю", "Действие необратимо")
        clear = small_button("Очистить")
        clear.clicked.connect(self._on_history_cleared)
        clear_row.add_control(clear)
        controls.add(clear_row)

        body.addWidget(controls)

    # --- вкладка «Настройки» ----------------------------------------------

    def _build_settings_pane(self, body: QVBoxLayout) -> None:
        body.addWidget(self._section("Запуск", first=True))
        startup = RowList()

        autostart_row = Row(
            "Запускать с Windows",
            "Записывает MeowsL в автозагрузку текущего пользователя",
        )
        self._autostart_switch = Switch(autostart.is_enabled_in_settings())
        self._autostart_switch.toggled_by_user.connect(self._on_autostart_toggled)
        autostart_row.add_control(self._autostart_switch)
        startup.add(autostart_row)

        show_row = Row(
            "Открывать это окно при запуске",
            "Выключено: при автозапуске MeowsL уходит сразу в трей",
        )
        self._show_switch = Switch(user_settings.show_window_on_start())
        self._show_switch.toggled_by_user.connect(self._on_show_on_start_toggled)
        show_row.add_control(self._show_switch)
        startup.add(show_row)
        body.addWidget(startup)

        body.addWidget(self._section("Перевод"))
        translate = RowList()

        pair_row = Row("Языковая пара", "Направление определяется автоматически")
        self._pair_box = self._combo(
            list(LANG_PAIR_CHOICES), user_settings.lang_pair(), self._on_pair_changed
        )
        pair_row.add_control(self._pair_box)
        translate.add(pair_row)

        debounce_row = Row(
            "Задержка перед переводом",
            "Пауза после последнего набранного символа",
        )
        self._debounce_box = self._combo(
            [(str(value), f"{value} мс") for value in DEBOUNCE_CHOICES],
            str(user_settings.debounce_ms()),
            self._on_debounce_changed,
        )
        debounce_row.add_control(self._debounce_box)
        translate.add(debounce_row)

        auto_row = Row(
            "Переводить текст из буфера сразу",
            "Иначе окно откроется с текстом, но без перевода",
        )
        self._auto_switch = Switch(user_settings.auto_translate())
        self._auto_switch.toggled_by_user.connect(self._on_auto_toggled)
        auto_row.add_control(self._auto_switch)
        translate.add(auto_row)
        body.addWidget(translate)

        body.addWidget(self._section("Перевод с экрана"))
        screen = RowList()

        ocr_row = Row(
            "Язык распознавания",
            "«Авто» распознаёт дважды и берёт более полный результат",
        )
        self._ocr_box = self._combo(
            list(OCR_LANG_CHOICES),
            user_settings.ocr_language(),
            self._on_ocr_lang_changed,
        )
        ocr_row.add_control(self._ocr_box)
        screen.add(ocr_row)

        self._ocr_packages_row = Row("Языковые пакеты OCR", "Проверяю…")
        self._ocr_pill = StatusPill("проверка", "idle")
        self._ocr_packages_row.add_control(self._ocr_pill)
        recheck = small_button("Проверить")
        recheck.clicked.connect(self._recheck_ocr)
        self._ocr_packages_row.add_control(recheck)
        screen.add(self._ocr_packages_row)

        sound_row = Row(
            "Звук после распознавания с экрана",
            "Сигнал, когда OCR закончил. Перевод из буфера звука не даёт",
        )
        self._sound_switch = Switch(user_settings.ocr_sound())
        self._sound_switch.toggled_by_user.connect(self._on_sound_toggled)
        sound_row.add_control(self._sound_switch)
        screen.add(sound_row)
        body.addWidget(screen)

        body.addWidget(self._section("Окно перевода"))
        popup = RowList()

        remember_row = Row(
            "Запоминать размер и позицию",
            "Иначе popup открывается 420 × 320 по центру экрана",
        )
        self._remember_switch = Switch(user_settings.remember_popup_geometry())
        self._remember_switch.toggled_by_user.connect(self._on_remember_toggled)
        remember_row.add_control(self._remember_switch)
        popup.add(remember_row)

        blur_row = Row(
            "Закрывать по клику мимо окна", "Esc и кнопка × работают всегда"
        )
        self._blur_switch = Switch(user_settings.close_popup_on_blur())
        self._blur_switch.toggled_by_user.connect(self._on_blur_toggled)
        blur_row.add_control(self._blur_switch)
        popup.add(blur_row)
        body.addWidget(popup)

    def _combo(
        self,
        choices: list[tuple[str, str]],
        current: str,
        on_change: Callable[[str], None],
    ) -> ArrowComboBox:
        box = ArrowComboBox()
        for value, label in choices:
            box.addItem(label, value)
        index = box.findData(current)
        box.setCurrentIndex(index if index >= 0 else 0)
        box.currentIndexChanged.connect(
            lambda _index, widget=box: on_change(widget.currentData())
        )
        return box

    # --- вкладка «О программе» --------------------------------------------

    def _build_about_pane(self, body: QVBoxLayout) -> None:
        mark = QLabel()
        mark.setPixmap(logo_pixmap(52))
        mark.setFixedSize(52, 52)
        mark.setScaledContents(True)

        name = QLabel(f"{APP_DISPLAY_NAME} {APP_VERSION}")
        name.setObjectName("statusTitle")
        name_font = QFont(self._font)
        name_font.setPixelSize(18)
        name_font.setBold(True)
        name.setFont(name_font)

        tagline = QLabel(
            "Фоновый переводчик для Windows: буфер обмена и текст с экрана, "
            "без открытия браузера."
        )
        tagline.setObjectName("statusDetail")
        tagline.setWordWrap(True)

        text = QVBoxLayout()
        text.setContentsMargins(0, 0, 0, 0)
        text.setSpacing(3)
        text.addWidget(name)
        text.addWidget(tagline)

        top = QHBoxLayout()
        top.setContentsMargins(0, 14, 0, 8)
        top.setSpacing(14)
        top.addWidget(mark, 0, Qt.AlignmentFlag.AlignTop)
        top.addLayout(text, 1)
        body.addLayout(top)

        body.addWidget(self._section("Обновления"))
        update_list = RowList()
        self._update_row = Row("Версия не проверялась", f"Установлена {APP_VERSION}")
        self._update_pill = StatusPill("нет данных", "idle")
        self._update_row.add_control(self._update_pill)
        self._update_button = small_button("Проверить")
        self._update_button.clicked.connect(self._check_updates)
        self._update_row.add_control(self._update_button)
        update_list.add(self._update_row)
        body.addWidget(update_list)

        body.addWidget(self._section("Диагностика"))
        self._diagnostics = RowList()
        body.addWidget(self._diagnostics)

        body.addWidget(self._section("Проект"))
        project = RowList()

        repo_row = Row("GitHub", GITHUB_URL.replace("https://", ""))
        repo = small_button("Открыть")
        repo.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(GITHUB_URL)))
        repo_row.add_control(repo)
        project.add(repo_row)

        data_row = Row("Папка данных", str(history.history_path().parent))
        data = small_button("Открыть")
        data.clicked.connect(self._open_data_dir)
        data_row.add_control(data)
        project.add(data_row)

        body.addWidget(project)

    # --- обновление содержимого -------------------------------------------

    def refresh(self) -> None:
        """Пересобирает всё, что могло измениться, пока окно было скрыто."""
        self._refresh_switches()
        self._refresh_capture_key_labels()
        self._refresh_history()
        self._refresh_ocr_check()
        self._refresh_diagnostics()

    def _refresh_switches(self) -> None:
        self._autostart_switch.set_checked_silently(autostart.is_enabled_in_settings())
        self._show_switch.set_checked_silently(user_settings.show_window_on_start())
        self._history_switch.set_checked_silently(user_settings.history_enabled())
        self._auto_switch.set_checked_silently(user_settings.auto_translate())
        self._sound_switch.set_checked_silently(user_settings.ocr_sound())
        self._remember_switch.set_checked_silently(
            user_settings.remember_popup_geometry()
        )
        self._blur_switch.set_checked_silently(user_settings.close_popup_on_blur())

    def _refresh_capture_key_labels(self) -> None:
        label = user_settings.capture_label()
        self._capture_keys.set_keys([label])
        self._capture_card_keys.set_keys([label])
        self._capture_row.set_subtitle(self._capture_subtitle())

    def _refresh_history(self) -> None:
        entries = history.load() if user_settings.history_enabled() else []
        self._fill_home_history(entries)
        self._fill_history_pane(entries)

    def _fill_home_history(self, entries: list[history.HistoryEntry]) -> None:
        self._home_history.clear()
        if not entries:
            self._home_history.add(self._empty_state("Здесь появятся ваши переводы"))
            return
        for entry in entries[:HISTORY_PREVIEW_ROWS]:
            self._home_history.add(
                HistoryRow(entry, self._open_from_history, self._copy_entry)
            )

    def _fill_history_pane(self, entries: list[history.HistoryEntry]) -> None:
        layout = self._history_groups_layout
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        if not entries:
            layout.addWidget(self._section("История", first=True))
            layout.addWidget(
                self._empty_state(
                    "Здесь появятся ваши переводы"
                    if user_settings.history_enabled()
                    else "Хранение истории выключено"
                )
            )
            return

        first = True
        for label, group in history.group_by_day(entries):
            layout.addWidget(self._section(label, first=first))
            first = False
            rows = RowList()
            for entry in group:
                rows.add(HistoryRow(entry, self._open_from_history, self._copy_entry))
            layout.addWidget(rows)

    def _empty_state(self, text: str) -> QWidget:
        label = QLabel(text)
        label.setObjectName("emptyState")
        label.setContentsMargins(0, 10, 0, 12)
        return label

    def _recheck_ocr(self) -> None:
        """Та же проверка, но с ответом пользователю — иначе кнопка немая."""
        self._refresh_ocr_check()
        self._toast_message(diagnostics.ocr_check().detail)

    def _refresh_ocr_check(self) -> None:
        check = diagnostics.ocr_check()
        self._ocr_packages_row.set_subtitle(check.detail)
        self._ocr_pill.set_state(
            "установлены" if check.ok else "не найдены", "ok" if check.ok else "warn"
        )
        self._update_status(check)

    def _update_status(self, ocr: diagnostics.Check) -> None:
        capture = user_settings.capture_label()
        if ocr.ok:
            self._status_dot.set_tone("ok")
            self._status_title.setText("Работает в фоне")
            self._status_detail.setText(
                f"Хоткеи Ctrl+C+C и {capture} активны · {ocr.detail}"
            )
            return

        self._status_dot.set_tone("warn")
        self._status_title.setText("Работает с ограничением")
        self._status_detail.setText(
            f"Хоткей Ctrl+C+C активен · {ocr.detail} — перевод с экрана недоступен"
        )

    def _refresh_diagnostics(self) -> None:
        self._diagnostics.clear()
        checks = [diagnostics.runtime_check(), diagnostics.build_check()]
        checks.append(diagnostics.ocr_check())
        checks.append(
            self._translator_check
            or diagnostics.Check("Переводчик", "Проверяю соединение…", True)
        )
        checks.append(
            diagnostics.Check(
                "Права",
                "администратор"
                if diagnostics.is_elevated()
                else "обычный пользователь",
                True,
            )
        )
        checks.append(diagnostics.Check("Настройки", user_settings.location(), True))

        for check in checks:
            row = Row(check.title, check.detail)
            row.add_control(
                StatusPill("ок" if check.ok else "ошибка", "ok" if check.ok else "warn")
            )
            self._diagnostics.add(row)

        diagnostics.probe_translator(self).done.connect(self._on_translator_probe)

    def _on_translator_probe(self, check: diagnostics.Check) -> None:
        self._translator_check = check
        if self.isVisible():
            self._refresh_diagnostics_row(check)

    def _refresh_diagnostics_row(self, check: diagnostics.Check) -> None:
        """Обновляет только строку переводчика, чтобы не пересобирать список."""
        for row in self._diagnostics.findChildren(Row):
            title = row.findChild(QLabel, "rowTitle")
            if title is not None and title.text() == "Переводчик":
                row.set_subtitle(check.detail)
                pill = row.findChild(StatusPill)
                if pill is not None:
                    pill.set_state(
                        "ок" if check.ok else "нет связи", "ok" if check.ok else "warn"
                    )
                return

    # --- обработчики ------------------------------------------------------

    def _select_pane(self, key: str) -> None:
        index = self._pane_index.get(key)
        if index is None:
            return
        self._stack.setCurrentIndex(index)
        button = self._nav_buttons.get(key)
        if button is not None:
            button.setChecked(True)

    def _toast_message(self, text: str) -> None:
        self._toast.setText(text)
        self._toast.adjustSize()
        x = (self._container.width() - self._toast.width()) // 2
        y = self._container.height() - self._toast.height() - MAIN_FOOTER_HEIGHT - 12
        self._toast.move(max(12, x), max(12, y))
        self._toast.setVisible(True)
        self._toast.raise_()
        self._toast_timer.start(_TOAST_MS)

    def _on_autostart_toggled(self, enabled: bool) -> None:
        autostart.set_enabled(enabled)
        self._toast_message("Автозапуск включён" if enabled else "Автозапуск выключен")

    def _on_show_on_start_toggled(self, enabled: bool) -> None:
        user_settings.set_show_window_on_start(enabled)
        autostart.sync()

    def _on_pair_changed(self, value: str) -> None:
        user_settings.set_lang_pair(value)

    def _on_debounce_changed(self, value: str) -> None:
        user_settings.set_debounce_ms(int(value))

    def _on_auto_toggled(self, enabled: bool) -> None:
        user_settings.set_auto_translate(enabled)

    def _on_ocr_lang_changed(self, value: str) -> None:
        user_settings.set_ocr_language(value)

    def _on_sound_toggled(self, enabled: bool) -> None:
        user_settings.set_ocr_sound(enabled)
        if enabled:
            play_notification()

    def _on_remember_toggled(self, enabled: bool) -> None:
        user_settings.set_remember_popup_geometry(enabled)

    def _on_blur_toggled(self, enabled: bool) -> None:
        user_settings.set_close_popup_on_blur(enabled)

    def _on_history_toggled(self, enabled: bool) -> None:
        user_settings.set_history_enabled(enabled)
        self._refresh_history()

    def _on_history_cleared(self) -> None:
        history.clear()
        self._refresh_history()
        self._toast_message("История очищена")

    def _open_from_history(self, entry: history.HistoryEntry) -> None:
        self.translate_text_requested.emit(entry.source)

    def _copy_entry(self, entry: history.HistoryEntry) -> None:
        clipboard = QGuiApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(entry.target)
        self._toast_message("Перевод скопирован")

    def _open_data_dir(self) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(history.history_path().parent)))

    def _restart_hotkeys(self) -> None:
        self.hotkeys_restart_requested.emit()
        self._toast_message("Хоткеи перерегистрированы")

    def _restart_elevated(self) -> None:
        if diagnostics.is_elevated():
            self._toast_message("MeowsL уже запущен от администратора")
            return
        if relaunch_as_admin():
            self.quit_requested.emit()
            return
        self._toast_message("Windows отклонила запрос на повышение прав")

    def _rebind_capture_key(self) -> None:
        """На время захвата снимаем свой хук, иначе он съест нажатие."""
        self.hotkeys_restart_requested.emit()
        dialog = KeyCaptureDialog(self)
        accepted = dialog.exec() == QDialog.DialogCode.Accepted
        captured = dialog.result_key()

        if accepted and captured is not None:
            scan_code, label = captured
            user_settings.set_capture_key(scan_code, label)
            self._refresh_capture_key_labels()
            self._toast_message(f"Перевод с экрана теперь на «{label}»")

        self.hotkeys_restart_requested.emit()

    def _check_updates(self) -> None:
        self._update_button.setEnabled(False)
        self._update_row.set_title("Проверяю GitHub…")
        self._update_pill.set_state("проверка", "idle")
        updates.check(self).done.connect(self._on_update_result)

    def _on_update_result(self, result: updates.UpdateResult) -> None:
        self._update_button.setEnabled(True)
        self._update_row.set_title(result.message)
        self._update_row.set_subtitle(f"Установлена {APP_VERSION}")

        if not result.ok:
            self._update_pill.set_state("ошибка", "warn")
        elif result.available:
            self._update_row.set_subtitle(
                f"Установлена {APP_VERSION} · страница релизов открыта в браузере"
            )
            self._update_pill.set_state("обновление", "warn")
            QDesktopServices.openUrl(QUrl(GITHUB_RELEASES_URL))
        else:
            self._update_pill.set_state("ок", "ok")

        self._toast_message(result.message)

    # --- показ и геометрия ------------------------------------------------

    def show_window(self, pane: Optional[str] = None) -> None:
        """Показывает окно, обновив содержимое перед появлением."""
        self._restore_geometry()
        self.refresh()
        if pane is not None:
            self._select_pane(pane)
        self.show()
        self.setWindowState(
            self.windowState() & ~Qt.WindowState.WindowMinimized
            | Qt.WindowState.WindowActive
        )
        self.raise_()
        self.activateWindow()

    def _setup_geometry_persistence(self) -> None:
        self._geometry_save = QTimer(self)
        self._geometry_save.setSingleShot(True)
        self._geometry_save.timeout.connect(self._persist_geometry)

    def _persist_geometry(self) -> None:
        store = user_settings.settings()
        store.setValue(SETTINGS_KEY_MAIN_GEOMETRY, self.saveGeometry())
        store.sync()

    def _restore_geometry(self) -> None:
        if self._geometry_restored:
            return
        self._geometry_restored = True

        raw = user_settings.settings().value(SETTINGS_KEY_MAIN_GEOMETRY)
        if isinstance(raw, QByteArray) and not raw.isEmpty():
            if self.restoreGeometry(raw) and not self.size().isEmpty():
                return

        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        center = screen.availableGeometry().center()
        self.move(center.x() - self.width() // 2, center.y() - self.height() // 2)

    def moveEvent(self, event) -> None:
        super().moveEvent(event)
        if self.isVisible():
            self._geometry_save.start(SETTINGS_GEOMETRY_SAVE_MS)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.isVisible():
            self._geometry_save.start(SETTINGS_GEOMETRY_SAVE_MS)

    def hideEvent(self, event) -> None:
        self._frameless_release_resize()
        self._persist_geometry()
        super().hideEvent(event)

    def closeEvent(self, event) -> None:
        """Крестик и Alt+F4 прячут окно — выход только из меню трея."""
        event.ignore()
        self.hide()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            return
        super().keyPressEvent(event)

    def shutdown(self) -> None:
        self._geometry_save.stop()
        self._toast_timer.stop()
        self._persist_geometry()

    # --- ресайз без рамки -------------------------------------------------

    def _install_resize_event_filters(self) -> None:
        self.installEventFilter(self)
        for child in self.findChildren(QWidget):
            child.installEventFilter(self)
            child.setMouseTracking(True)

    def eventFilter(self, watched: QObject, event) -> bool:
        event_type = event.type()
        if event_type not in (
            QEvent.Type.MouseMove,
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseButtonRelease,
        ):
            return super().eventFilter(watched, event)

        if not self.isVisible():
            return super().eventFilter(watched, event)

        local_pos = self.mapFromGlobal(event.globalPosition().toPoint())
        global_pos = event.globalPosition().toPoint()
        watched_widget = watched if isinstance(watched, QWidget) else None

        if event_type == QEvent.Type.MouseButtonPress:
            if self._frameless_press_at(
                local_pos, global_pos, event.button(), watched_widget
            ):
                return True
        elif event_type == QEvent.Type.MouseMove:
            if self._frameless_move_at(local_pos, global_pos, watched_widget):
                return True
        elif event_type == QEvent.Type.MouseButtonRelease:
            if self._frameless_release_resize(watched_widget):
                return True

        return super().eventFilter(watched, event)

    def mousePressEvent(self, event) -> None:
        if self._frameless_mouse_press(event):
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._frameless_mouse_move(event):
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._frameless_mouse_release(event)
        super().mouseReleaseEvent(event)
