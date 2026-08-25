"""Custom resize для frameless-окна: все края и углы."""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QPushButton, QWidget

from translate_meows.config import RESIZE_CORNER, RESIZE_MARGIN, WINDOW_MARGIN
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

    def _widget_blocks_resize(self, watched: Optional[QWidget]) -> bool:
        """Кнопки закрытия/свопа/копирования не должны начинать ресайз."""
        widget: Optional[QWidget] = watched
        while widget is not None and widget is not self:
            if isinstance(widget, QPushButton):
                return True
            widget = widget.parentWidget()
        return False

    def _hit_resize_edge(self, pos) -> Optional[str]:
        """Hit-test по видимой плашке: углы больше краёв, как у окон Windows."""
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        if x < 0 or y < 0 or x >= w or y >= h:
            return None

        inset = WINDOW_MARGIN
        dist_left = x - inset
        dist_right = (w - inset) - x
        dist_top = y - inset
        dist_bottom = (h - inset) - y

        near_left = dist_left < RESIZE_MARGIN
        near_right = dist_right < RESIZE_MARGIN
        near_top = dist_top < RESIZE_MARGIN
        near_bottom = dist_bottom < RESIZE_MARGIN

        in_left_corner = dist_left < RESIZE_CORNER
        in_right_corner = dist_right < RESIZE_CORNER
        in_top_corner = dist_top < RESIZE_CORNER
        in_bottom_corner = dist_bottom < RESIZE_CORNER

        if in_top_corner and in_left_corner:
            return "top-left"
        if in_top_corner and in_right_corner:
            return "top-right"
        if in_bottom_corner and in_left_corner:
            return "bottom-left"
        if in_bottom_corner and in_right_corner:
            return "bottom-right"
        if near_left:
            return "left"
        if near_right:
            return "right"
        if near_top:
            return "top"
        if near_bottom:
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

    def _frameless_press_at(
        self, local_pos, global_pos, button, watched: Optional[QWidget] = None
    ) -> bool:
        if self._use_native_resize or button != Qt.MouseButton.LeftButton:
            return False
        if self._widget_blocks_resize(watched):
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

        if self._widget_blocks_resize(watched):
            self._update_resize_cursor(None, watched)
            return False

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
            self,
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
        parts = set(edge.split("-"))

        if "left" in parts:
            new_w = max(min_w, w - dx)
            x = geom.x() + (w - new_w)
            w = new_w
        elif "right" in parts:
            w = max(min_w, w + dx)

        if "top" in parts:
            new_h = max(min_h, h - dy)
            y = geom.y() + (h - new_h)
            h = new_h
        elif "bottom" in parts:
            h = max(min_h, h + dy)

        self.setGeometry(x, y, w, h)
