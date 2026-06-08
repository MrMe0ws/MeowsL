"""Custom resize для frameless-окна: все края и углы."""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QWidget

from translate_meows.config import RESIZE_MARGIN
from translate_meows.platform.win_native_resize import (
    handle_win_native_resize,
    is_win_native_resize_available,
)

_EDGE_CURSORS: dict[str, Qt.CursorShape] = {
    "left": Qt.CursorShape.SizeHorCursor,
    "right": Qt.CursorShape.SizeHorCursor,
    "top": Qt.CursorShape.SizeVerCursor,
    "bottom": Qt.CursorShape.SizeVerCursor,
    "top-left": Qt.CursorShape.SizeFDiagCursor,
    "bottom-right": Qt.CursorShape.SizeFDiagCursor,
    "top-right": Qt.CursorShape.SizeBDiagCursor,
    "bottom-left": Qt.CursorShape.SizeBDiagCursor,
}


class FramelessResizeMixin:
    """Миксин: hit-test и geometry-логика ресайза по краям окна."""

    _resize_edge: Optional[str]
    _resize_origin: Optional[object]
    _resize_start_geom: Optional[object]

    def _init_frameless_resize(self) -> None:
        self._resize_edge = None
        self._resize_origin = None
        self._resize_start_geom = None
        self._use_native_resize = is_win_native_resize_available()
        self.setMouseTracking(True)

    def uses_native_resize(self) -> bool:
        return self._use_native_resize

    def _hit_resize_edge(self, pos) -> Optional[str]:
        margin = RESIZE_MARGIN
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()

        left = x >= 0 and x < margin
        right = x >= w - margin and x < w
        top = y >= 0 and y < margin
        bottom = y >= h - margin and y < h

        if top and left:
            return "top-left"
        if top and right:
            return "top-right"
        if bottom and left:
            return "bottom-left"
        if bottom and right:
            return "bottom-right"
        if left:
            return "left"
        if right:
            return "right"
        if top:
            return "top"
        if bottom:
            return "bottom"
        return None

    def _cursor_for_edge(self, edge: Optional[str]) -> Qt.CursorShape:
        if edge is None:
            return Qt.CursorShape.ArrowCursor
        return _EDGE_CURSORS.get(edge, Qt.CursorShape.ArrowCursor)

    def _update_resize_cursor(
        self, edge: Optional[str], watched: Optional[QWidget] = None
    ) -> None:
        assert isinstance(self, QWidget)
        cursor = QCursor(self._cursor_for_edge(edge))
        self.setCursor(cursor)
        if watched is not None:
            if edge:
                watched.setCursor(cursor)
            else:
                watched.unsetCursor()

    def _frameless_press_at(self, local_pos, global_pos, button) -> bool:
        if self._use_native_resize or button != Qt.MouseButton.LeftButton:
            return False

        edge = self._hit_resize_edge(local_pos)
        if not edge:
            return False

        self._resize_edge = edge
        self._resize_origin = global_pos
        self._resize_start_geom = self.geometry()
        assert isinstance(self, QWidget)
        self.grabMouse()
        self.grabKeyboard()
        return True

    def _frameless_move_at(
        self, local_pos, global_pos, watched: Optional[QWidget] = None
    ) -> bool:
        if self._use_native_resize:
            return False

        if self._resize_edge and self._resize_origin and self._resize_start_geom:
            self._apply_resize_delta(global_pos - self._resize_origin)
            return True

        edge = self._hit_resize_edge(local_pos)
        self._update_resize_cursor(edge, watched)
        return False

    def _frameless_release_resize(self, watched: Optional[QWidget] = None) -> bool:
        was_resizing = self._resize_edge is not None
        if was_resizing:
            assert isinstance(self, QWidget)
            self.releaseMouse()
            self.releaseKeyboard()
        self._resize_edge = None
        self._resize_origin = None
        self._resize_start_geom = None
        self._update_resize_cursor(None, watched)
        return was_resizing

    def _frameless_native_event(self, event_type, message):
        """Обработка WM_NCHITTEST. Нельзя вызывать super().nativeEvent() — на
        PyQt6/Windows это приводит к STATUS_FATAL_USER_CALLBACK_EXCEPTION."""
        assert isinstance(self, QWidget)
        if not self._use_native_resize:
            return False, 0
        handled = handle_win_native_resize(
            self, event_type, message, self._hit_resize_edge
        )
        if handled is not None:
            return handled
        return False, 0

    def _frameless_mouse_press(self, event) -> bool:
        if self._frameless_press_at(
            event.position().toPoint(),
            event.globalPosition().toPoint(),
            event.button(),
        ):
            event.accept()
            return True
        return False

    def _frameless_mouse_move(self, event) -> bool:
        if self._frameless_move_at(
            event.position().toPoint(), event.globalPosition().toPoint()
        ):
            event.accept()
            return True
        return False

    def _frameless_mouse_release(self, event) -> None:
        self._frameless_release_resize()

    def _apply_resize_delta(self, delta) -> None:
        assert isinstance(self, QWidget)
        geom = self._resize_start_geom
        edge = self._resize_edge
        if geom is None or edge is None:
            return

        min_w = self.minimumWidth()
        min_h = self.minimumHeight()

        x, y = geom.x(), geom.y()
        w, h = geom.width(), geom.height()
        dx, dy = delta.x(), delta.y()

        if "left" in edge:
            new_w = max(min_w, w - dx)
            x = geom.x() + (w - new_w)
            w = new_w
        elif "right" in edge:
            w = max(min_w, w + dx)

        if "top" in edge:
            new_h = max(min_h, h - dy)
            y = geom.y() + (h - new_h)
            h = new_h
        elif "bottom" in edge:
            h = max(min_h, h + dy)

        self.setGeometry(x, y, w, h)
