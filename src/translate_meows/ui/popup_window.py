"""Минималистичное всплывающее окно перевода."""

from typing import Optional

from PyQt6.QtCore import QEvent, QObject, QTimer, Qt, QRect
from PyQt6.QtGui import QGuiApplication, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from translate_meows.config import (
    DEBOUNCE_MS,
    LANG_DISPLAY,
    POPUP_HEIGHT,
    POPUP_MIN_HEIGHT,
    POPUP_MIN_WIDTH,
    POPUP_WIDTH,
    SETTINGS_GEOMETRY_SAVE_MS,
    WINDOW_MARGIN,
)
from translate_meows.platform.window_state import (
    center_popup_on_screen,
    ensure_popup_on_screen,
    load_popup_geometry,
    place_popup_near_rect,
    save_popup_geometry,
)
from translate_meows.services.translation_runner import TranslationRunner
from translate_meows.services.translator import resolve_direction
from translate_meows.ui.fonts import app_font
from translate_meows.ui.icons import app_icon
from translate_meows.ui.styles import POPUP_STYLESHEET
from translate_meows.ui.widgets.frameless_resize import FramelessResizeMixin
from translate_meows.ui.widgets.text_panel import TextPanel
from translate_meows.ui.widgets.title_bar import TitleBar


def _is_widget_alive(widget: Optional[QWidget]) -> bool:
    if widget is None:
        return False
    try:
        widget.isVisible()
    except RuntimeError:
        return False
    return True


class PopupDismissFilter(QObject):
    """Закрывает popup по Esc и клику вне окна."""

    def __init__(self, popup: QWidget) -> None:
        super().__init__(popup)
        self._popup = popup
        self._active = True

    def deactivate(self) -> None:
        self._active = False
        self._popup = None

    def eventFilter(self, watched: QObject, event) -> bool:
        if not self._active or not _is_widget_alive(self._popup):
            return False

        if not self._popup.isVisible():
            return False

        if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Escape:
            self._popup.hide()
            return True

        if event.type() == QEvent.Type.MouseButtonPress:
            global_pos = event.globalPosition().toPoint()
            if not self._popup.frameGeometry().contains(global_pos):
                self._popup.hide()
                return False

        return False


class TranslationPopup(FramelessResizeMixin, QWidget):
    """Frameless popup: скруглённая плашка, ресайз со всех сторон."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._init_frameless_resize()

        self._runner = TranslationRunner(self)
        self._runner.finished.connect(self._on_translation_done)
        self._runner.error.connect(self._on_translation_error)

        self._request_id = 0
        self._source_lang: Optional[str] = None
        self._target_lang: Optional[str] = None
        self._direction_locked = False
        self._dismiss_filter = PopupDismissFilter(self)
        self._app: Optional[QGuiApplication] = None
        self._has_saved_geometry = False
        self._geometry_restored = False

        self._build_ui()
        self._setup_geometry_persistence()
        self._setup_debounce()
        self._setup_dismiss()

    def _build_ui(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowIcon(app_icon())
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumSize(POPUP_MIN_WIDTH, POPUP_MIN_HEIGHT)
        self.resize(POPUP_WIDTH, POPUP_HEIGHT)

        font = app_font(10)

        container = QWidget(self)
        container.setObjectName("container")
        container.setMouseTracking(True)

        title_bar = TitleBar(self, container, font=font)

        swap_btn = QPushButton("⇄")
        swap_btn.setObjectName("headerBtn")
        swap_btn.setToolTip("Поменять тексты и направление перевода")
        swap_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        swap_btn.clicked.connect(self._swap_texts)

        close_btn = QPushButton("×")
        close_btn.setObjectName("closeBtn")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.hide)

        header = QHBoxLayout()
        header.setContentsMargins(8, 4, 6, 0)
        header.setSpacing(2)
        header.addWidget(title_bar, stretch=1)
        header.addWidget(swap_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

        self._input_panel = TextPanel(
            "input",
            "Введите текст…",
            font,
            LANG_DISPLAY["en"],
            editable=True,
            on_copy=lambda: self._copy_text(self._input_panel.editor),
        )
        self._output_panel = TextPanel(
            "output",
            "Перевод…",
            font,
            LANG_DISPLAY["ru"],
            editable=False,
            on_copy=lambda: self._copy_text(self._output_panel.editor),
        )
        self._input = self._input_panel.editor
        self._output = self._output_panel.editor

        divider = QFrame()
        divider.setObjectName("fieldDivider")
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFixedHeight(1)

        body = QVBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._input_panel, stretch=1)
        body.addWidget(divider)
        body.addWidget(self._output_panel, stretch=1)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(header)
        layout.addLayout(body, stretch=1)

        root = QVBoxLayout(self)
        root.setContentsMargins(WINDOW_MARGIN, WINDOW_MARGIN, WINDOW_MARGIN, WINDOW_MARGIN)
        root.addWidget(container)

        self.setStyleSheet(POPUP_STYLESHEET)
        self._input.textChanged.connect(self._on_text_changed)
        if not self.uses_native_resize():
            self._install_resize_event_filters()

    def _setup_geometry_persistence(self) -> None:
        self._geometry_save = QTimer(self)
        self._geometry_save.setSingleShot(True)
        self._geometry_save.timeout.connect(self._persist_geometry)

    def _persist_geometry(self) -> None:
        save_popup_geometry(self)

    def _schedule_geometry_save(self) -> None:
        self._geometry_save.start(SETTINGS_GEOMETRY_SAVE_MS)

    def _restore_or_default_geometry(self) -> None:
        if self._geometry_restored:
            ensure_popup_on_screen(self)
            return

        self._geometry_restored = True
        self._has_saved_geometry = load_popup_geometry(self)
        if self._has_saved_geometry:
            ensure_popup_on_screen(self)
        else:
            center_popup_on_screen(self)

    def _install_resize_event_filters(self) -> None:
        """Ресайз по краям окна — события ловим и на дочерних виджетах."""
        self.installEventFilter(self)
        for child in self.findChildren(QWidget):
            child.installEventFilter(self)
            child.setMouseTracking(True)

    def eventFilter(self, watched: QObject, event) -> bool:
        if not _is_widget_alive(self):
            return False

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

    def hideEvent(self, event) -> None:
        self._frameless_release_resize()
        self._persist_geometry()
        super().hideEvent(event)

    def moveEvent(self, event) -> None:
        super().moveEvent(event)
        if self.isVisible():
            self._schedule_geometry_save()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.isVisible():
            self._schedule_geometry_save()

    def _setup_dismiss(self) -> None:
        app = QGuiApplication.instance()
        self._app = app
        if app is not None:
            app.installEventFilter(self._dismiss_filter)
            app.focusChanged.connect(self._on_focus_changed)

        esc = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        esc.setContext(Qt.ShortcutContext.ApplicationShortcut)
        esc.activated.connect(self.hide)

    def _on_focus_changed(self, _old: QWidget, new: Optional[QWidget]) -> None:
        if not _is_widget_alive(self) or not self.isVisible():
            return
        if new is None:
            self.hide()
            return
        if new is not self and not self.isAncestorOf(new):
            self.hide()

    def _setup_debounce(self) -> None:
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.timeout.connect(self._start_translation)

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

    def show_with_text(
        self,
        text: str,
        *,
        auto_translate: bool = True,
        anchor_rect: QRect | None = None,
    ) -> None:
        """Показать окно и при необходимости запустить перевод."""
        self._reset_session()
        if anchor_rect is not None:
            self.resize(POPUP_WIDTH, POPUP_HEIGHT)
        else:
            self._restore_or_default_geometry()

        self._input.blockSignals(True)
        self._input.setPlainText(text)
        self._input.blockSignals(False)

        if auto_translate and text.strip():
            self._start_translation()
        else:
            self._output.clear()
            self._update_lang_labels()

        self.show()
        if anchor_rect is not None:
            place_popup_near_rect(self, anchor_rect)
            ensure_popup_on_screen(self)
        elif not self._has_saved_geometry:
            center_popup_on_screen(self)
            ensure_popup_on_screen(self)
        self.raise_()
        self.activateWindow()
        self._input.setFocus()

    def _reset_session(self) -> None:
        self._debounce.stop()
        self._request_id += 1
        self._source_lang = None
        self._target_lang = None
        self._direction_locked = False

    def shutdown(self) -> None:
        """Корректно останавливает фоновый поток и снимает глобальные хуки."""
        self._debounce.stop()
        self._geometry_save.stop()
        self._persist_geometry()
        self._request_id += 1
        self._frameless_release_resize()
        self._teardown_dismiss()
        if not self.uses_native_resize():
            self._teardown_resize_event_filters()
        self._runner.shutdown()

    def _teardown_dismiss(self) -> None:
        self._dismiss_filter.deactivate()
        app = self._app
        if app is None:
            return
        app.removeEventFilter(self._dismiss_filter)
        try:
            app.focusChanged.disconnect(self._on_focus_changed)
        except TypeError:
            pass

    def _teardown_resize_event_filters(self) -> None:
        self.removeEventFilter(self)
        for child in self.findChildren(QWidget):
            child.removeEventFilter(self)

    def _lang_name(self, code: Optional[str]) -> str:
        if not code:
            return "···"
        return LANG_DISPLAY.get(code, code.upper())

    def _update_lang_labels(self) -> None:
        self._input_panel.set_lang_label(self._lang_name(self._source_lang))
        self._output_panel.set_lang_label(self._lang_name(self._target_lang))

    def _on_text_changed(self) -> None:
        self._debounce.stop()
        text = self._input.toPlainText().strip()
        if not text:
            self._request_id += 1
            self._output.clear()
            if not self._direction_locked:
                self._source_lang = None
                self._target_lang = None
            self._update_lang_labels()
            return

        if not self._direction_locked:
            self._source_lang = None
            self._target_lang = None

        self._debounce.start(DEBOUNCE_MS)

    def _swap_texts(self) -> None:
        try:
            self._debounce.stop()
            self._request_id += 1

            input_text = self._input.toPlainText()
            output_text = self._output.toPlainText()

            self._input.blockSignals(True)
            self._input.setPlainText(output_text)
            self._input.blockSignals(False)
            self._output.setPlainText(input_text)

            if self._source_lang and self._target_lang:
                self._source_lang, self._target_lang = (
                    self._target_lang,
                    self._source_lang,
                )
            elif input_text.strip():
                src, tgt = resolve_direction(input_text.strip())
                self._source_lang, self._target_lang = tgt, src
            else:
                self._source_lang, self._target_lang = "en", "ru"

            self._direction_locked = True
            self._update_lang_labels()

            if output_text.strip():
                self._start_translation()
        except Exception:
            pass

    def _copy_text(self, field) -> None:
        try:
            text = field.toPlainText()
            if not text:
                return
            clipboard = QGuiApplication.clipboard()
            if clipboard is not None:
                clipboard.setText(text)
        except Exception:
            pass

    def _start_translation(self) -> None:
        try:
            text = self._input.toPlainText().strip()
            if not text:
                return

            self._request_id += 1
            request_id = self._request_id

            if self._direction_locked and self._source_lang and self._target_lang:
                source, target = self._source_lang, self._target_lang
            else:
                source, target = resolve_direction(text)
                self._source_lang, self._target_lang = source, target

            self._update_lang_labels()
            self._runner.submit(text, request_id, source, target)
        except Exception:
            pass

    def _on_translation_done(self, result: str, request_id: int) -> None:
        if request_id != self._request_id:
            return
        self._output.setPlainText(result)
        self._update_lang_labels()

    def _on_translation_error(self, message: str, request_id: int) -> None:
        if request_id != self._request_id:
            return
        self._output.setPlainText(message)
