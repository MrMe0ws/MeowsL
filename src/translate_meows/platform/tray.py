"""Иконка в системном трее Windows."""

from typing import Callable

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon

from translate_meows.config import APP_NAME
from translate_meows.ui.icons import app_icon


class TrayManager:
    """Управляет иконкой в трее и контекстным меню."""

    def __init__(
        self,
        on_show: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        self._tray = QSystemTrayIcon(app_icon())
        self._tray.setToolTip(APP_NAME)

        menu = QMenu()
        show_action = QAction("Перевести из буфера (Ctrl+C+C)", menu)
        show_action.triggered.connect(on_show)
        quit_action = QAction("Выход", menu)
        quit_action.triggered.connect(on_quit)

        menu.addAction(show_action)
        menu.addSeparator()
        menu.addAction(quit_action)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(
            lambda reason: on_show()
            if reason == QSystemTrayIcon.ActivationReason.Trigger
            else None
        )

    def show(self) -> None:
        self._tray.show()

    def hide(self) -> None:
        self._tray.hide()
