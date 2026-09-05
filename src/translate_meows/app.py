"""Точка сборки приложения: трей, хоткеи, главное окно, popup."""

import sys

from PyQt6.QtCore import QObject, Qt, QRect, pyqtSignal
from PyQt6.QtGui import QGuiApplication, QImage
from PyQt6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

from translate_meows import settings as user_settings
from translate_meows.config import APP_NAME, TRAY_ARG
from translate_meows.platform import autostart
from translate_meows.platform.app_id import set_app_user_model_id
from translate_meows.platform.hotkey import HotkeyListener
from translate_meows.platform.power_resume import install_power_resume_handler
from translate_meows.platform.sound import play_notification
from translate_meows.platform.tray import TrayManager
from translate_meows.services.ocr_runner import OcrRunner
from translate_meows.ui.icons import app_icon
from translate_meows.ui.main_window import MainWindow
from translate_meows.ui.popup_window import TranslationPopup
from translate_meows.ui.screen_capture_overlay import ScreenCaptureOverlay

OCR_EMPTY_MESSAGE = "Текст не распознан"


class HotkeyBridge(QObject):
    """Мост между потоком keyboard и главным потоком Qt."""

    triggered = pyqtSignal()
    screen_capture_triggered = pyqtSignal()


class TranslatorApp:
    """Оркестратор фонового переводчика."""

    def __init__(self, argv: list[str]) -> None:
        set_app_user_model_id()
        self._app = QApplication(argv)
        self._app.setApplicationName(APP_NAME)
        self._app.setWindowIcon(app_icon())
        self._app.setQuitOnLastWindowClosed(False)
        self._app.setStyle("Fusion")

        self._start_in_tray = TRAY_ARG in argv[1:]
        self._shutting_down = False
        self._popup = TranslationPopup()
        self._main_window = MainWindow()
        self._overlay = ScreenCaptureOverlay()
        self._ocr_runner = OcrRunner(self._app)
        self._ocr_request_id = 0
        self._capture_anchor: QRect | None = None

        self._bridge = HotkeyBridge()
        self._bridge.triggered.connect(
            self._on_hotkey_triggered, Qt.ConnectionType.QueuedConnection
        )
        self._bridge.screen_capture_triggered.connect(
            self._on_screen_capture_triggered, Qt.ConnectionType.QueuedConnection
        )

        self._overlay.region_captured.connect(self._on_region_captured)
        self._ocr_runner.finished.connect(self._on_ocr_finished)
        self._ocr_runner.error.connect(self._on_ocr_error)

        self._hotkey = HotkeyListener(
            on_trigger=self._bridge.triggered.emit,
            on_screen_capture=self._bridge.screen_capture_triggered.emit,
        )
        self._power_resume = install_power_resume_handler(
            self._app, self._hotkey.restart
        )
        self._tray = TrayManager(
            on_open_main=self._on_open_main_window,
            on_show=self._on_hotkey_triggered,
            on_capture=self._on_screen_capture_triggered,
            on_quit=self._app.quit,
        )

        self._main_window.translate_clipboard_requested.connect(
            self._on_hotkey_triggered
        )
        self._main_window.screen_capture_requested.connect(
            self._on_capture_from_window
        )
        self._main_window.hotkeys_restart_requested.connect(self._hotkey.restart)
        self._main_window.translate_text_requested.connect(self._on_translate_text)
        self._main_window.quit_requested.connect(self._app.quit)

        self._app.aboutToQuit.connect(self._on_about_to_quit)

    def run(self) -> int:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(
                None,
                APP_NAME,
                "Системный трей недоступен. Приложение не может работать в фоне.",
            )
            return 1

        autostart.sync()
        self._tray.show()
        self._hotkey.start()

        if self._should_show_window():
            self._main_window.show_window()

        return self._app.exec()

    def _should_show_window(self) -> bool:
        """При автозапуске окно появляется только если так настроено."""
        if not self._start_in_tray:
            return True
        return user_settings.show_window_on_start()

    def _on_about_to_quit(self) -> None:
        if self._shutting_down:
            return
        self._shutting_down = True

        self._hotkey.stop()
        if self._power_resume is not None:
            self._power_resume.cleanup()
            self._power_resume = None

        self._overlay.dismiss()
        self._ocr_request_id += 1
        self._ocr_runner.finished.disconnect(self._on_ocr_finished)
        self._ocr_runner.error.disconnect(self._on_ocr_error)

        self._main_window.shutdown()
        self._popup.shutdown()
        self._ocr_runner.shutdown(timeout_ms=15000)
        self._tray.hide()

    def _on_open_main_window(self) -> None:
        self._main_window.show_window()

    def _on_hotkey_triggered(self) -> None:
        clipboard = QGuiApplication.clipboard()
        text = clipboard.text() if clipboard else ""
        self._popup.show_with_text(
            text, auto_translate=user_settings.auto_translate()
        )

    def _on_translate_text(self, text: str) -> None:
        """Повторное открытие перевода из истории."""
        self._popup.show_with_text(text)

    def _on_capture_from_window(self) -> None:
        """Главное окно уходит с дороги, иначе оно попадёт в снимок экрана."""
        self._main_window.hide()
        self._on_screen_capture_triggered()

    def _on_screen_capture_triggered(self) -> None:
        if self._overlay.isVisible():
            return
        self._overlay.show_overlay()

    def _on_region_captured(self, image: QImage, selection: QRect) -> None:
        self._capture_anchor = selection
        self._ocr_request_id += 1
        self._ocr_runner.submit(image, self._ocr_request_id)

    def _on_ocr_finished(self, text: str, request_id: int) -> None:
        if request_id != self._ocr_request_id:
            return
        anchor = self._capture_anchor
        self._capture_anchor = None
        if text.strip():
            self._notify_ocr_done()
            self._popup.show_with_text(text, anchor_rect=anchor)
            return
        self._popup.show_with_text(
            OCR_EMPTY_MESSAGE, auto_translate=False, anchor_rect=anchor
        )

    def _on_ocr_error(self, message: str, request_id: int) -> None:
        if request_id != self._ocr_request_id:
            return
        anchor = self._capture_anchor
        self._capture_anchor = None
        self._popup.show_with_text(
            message, auto_translate=False, anchor_rect=anchor
        )

    def _notify_ocr_done(self) -> None:
        if not user_settings.ocr_sound():
            return
        play_notification()


def run() -> int:
    return TranslatorApp(sys.argv).run()
