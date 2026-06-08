"""Точка сборки приложения: трей, хоткеи, popup."""

import sys

from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

from translate_meows.config import APP_NAME
from translate_meows.platform.hotkey import HotkeyListener
from translate_meows.platform.tray import TrayManager
from translate_meows.ui.icons import app_icon
from translate_meows.ui.popup_window import TranslationPopup


class HotkeyBridge(QObject):
    """Мост между потоком keyboard и главным потоком Qt."""

    triggered = pyqtSignal()


class TranslatorApp:
    """Оркестратор фонового переводчика."""

    def __init__(self) -> None:
        self._app = QApplication(sys.argv)
        self._app.setApplicationName(APP_NAME)
        self._app.setWindowIcon(app_icon())
        self._app.setQuitOnLastWindowClosed(False)
        self._app.setStyle("Fusion")

        self._popup = TranslationPopup()
        self._bridge = HotkeyBridge()
        self._bridge.triggered.connect(
            self._on_hotkey_triggered, Qt.ConnectionType.QueuedConnection
        )

        self._hotkey = HotkeyListener(on_trigger=self._bridge.triggered.emit)
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

        self._tray.show()
        self._hotkey.start()
        return self._app.exec()

    def _on_about_to_quit(self) -> None:
        self._hotkey.stop()
        self._popup.shutdown()

    def _on_hotkey_triggered(self) -> None:
        clipboard = QGuiApplication.clipboard()
        text = clipboard.text() if clipboard else ""
        self._popup.show_with_text(text)


def run() -> int:
    return TranslatorApp().run()
