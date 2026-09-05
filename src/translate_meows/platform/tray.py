"""Иконка в системном трее Windows."""

from typing import Callable

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon

from translate_meows.config import APP_NAME
from translate_meows.platform import autostart
from translate_meows.ui.icons import app_icon


class TrayManager:
    """Управляет иконкой в трее и контекстным меню."""

    def __init__(
        self,
        on_open_main: Callable[[], None],
        on_show: Callable[[], None],
        on_capture: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        self._tray = QSystemTrayIcon(app_icon())
        self._tray.setToolTip(APP_NAME)

        menu = QMenu()
        open_action = QAction("Открыть MeowsL", menu)
        open_action.triggered.connect(on_open_main)

        show_action = QAction("Перевести из буфера (Ctrl+C+C)", menu)
        show_action.triggered.connect(on_show)

        capture_action = QAction("Перевести с экрана", menu)
        capture_action.triggered.connect(on_capture)

        self._autostart_action = QAction("Запускать с Windows", menu)
        self._autostart_action.setCheckable(True)
        self._autostart_action.setChecked(autostart.is_enabled_in_settings())
        self._autostart_action.triggered.connect(self._on_autostart_toggled)

        quit_action = QAction("Выход", menu)
        quit_action.triggered.connect(on_quit)

        menu.addAction(open_action)
        menu.addSeparator()
        menu.addAction(show_action)
        menu.addAction(capture_action)
        menu.addSeparator()
        menu.addAction(self._autostart_action)
        menu.addSeparator()
        menu.addAction(quit_action)

        menu.aboutToShow.connect(self._sync_autostart_state)

        self._menu = menu
        self._tray.setContextMenu(menu)
        self._tray.activated.connect(
            lambda reason: on_open_main()
            if reason == QSystemTrayIcon.ActivationReason.Trigger
            else None
        )

    def _sync_autostart_state(self) -> None:
        """Галочку могли переключить в окне настроек."""
        self._autostart_action.setChecked(autostart.is_enabled_in_settings())

    def _on_autostart_toggled(self, enabled: bool) -> None:
        autostart.set_enabled(enabled)

    def show(self) -> None:
        self._tray.show()

    def hide(self) -> None:
        self._tray.hide()
