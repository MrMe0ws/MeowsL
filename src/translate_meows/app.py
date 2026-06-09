"""Точка сборки приложения: трей, хоткеи, popup."""

import sys

from PyQt6.QtCore import QObject, Qt, QRect, pyqtSignal
from PyQt6.QtGui import QGuiApplication, QImage
from PyQt6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

from translate_meows.config import APP_NAME
from translate_meows.platform import autostart
from translate_meows.platform.hotkey import HotkeyListener
from translate_meows.platform.tray import TrayManager
from translate_meows.services.ocr_runner import OcrRunner
from translate_meows.ui.icons import app_icon
from translate_meows.ui.popup_window import TranslationPopup
from translate_meows.ui.screen_capture_overlay import ScreenCaptureOverlay

OCR_EMPTY_MESSAGE = "Текст не распознан"


class HotkeyBridge(QObject):
    """Мост между потоком keyboard и главным потоком Qt."""

    triggered = pyqtSignal()
    screen_capture_triggered = pyqtSignal()


class TranslatorApp:
    """Оркестратор фонового переводчика."""

    def __init__(self) -> None:
        self._app = QApplication(sys.argv)
        self._app.setApplicationName(APP_NAME)
        self._app.setWindowIcon(app_icon())
        self._app.setQuitOnLastWindowClosed(False)
        self._app.setStyle("Fusion")

        self._popup = TranslationPopup()
        self._overlay = ScreenCaptureOverlay()
        self._ocr_runner = OcrRunner()
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
        self._tray = TrayManager(
            on_show=self._on_hotkey_triggered,
            on_quit=self._app.quit,
        )
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
        return self._app.exec()

    def _on_about_to_quit(self) -> None:
        self._hotkey.stop()
        self._overlay.dismiss()
        self._ocr_request_id += 1
        self._ocr_runner.shutdown(timeout_ms=15000)
        self._popup.shutdown()

    def _on_hotkey_triggered(self) -> None:
        clipboard = QGuiApplication.clipboard()
        text = clipboard.text() if clipboard else ""
        self._popup.show_with_text(text)

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


def run() -> int:
    return TranslatorApp().run()
