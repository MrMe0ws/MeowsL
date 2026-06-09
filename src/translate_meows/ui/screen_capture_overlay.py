"""Полноэкранный оверлей для выделения области экрана."""

from PyQt6.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QGuiApplication, QImage, QPainter, QPen
from PyQt6.QtWidgets import QApplication, QWidget

from translate_meows.config import MIN_SELECTION_SIZE


def virtual_desktop_geometry() -> QRect:
    """Объединённая геометрия всех мониторов."""
    geometry = QRect()
    for screen in QGuiApplication.screens():
        geometry = geometry.united(screen.geometry())
    return geometry


def normalize_rect(start: QPoint, end: QPoint) -> QRect:
    """Нормализует прямоугольник выделения по двум углам."""
    return QRect(start, end).normalized()


def capture_region(global_rect: QRect) -> QImage:
    """Захватывает область экрана с учётом HiDPI и нескольких мониторов."""
    if global_rect.isEmpty():
        return QImage()

    image = QImage(global_rect.size(), QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    captured_any = False

    painter = QPainter(image)
    for screen in QGuiApplication.screens():
        screen_geom = screen.geometry()
        intersection = global_rect.intersected(screen_geom)
        if intersection.isEmpty():
            continue

        local_x = intersection.x() - screen_geom.x()
        local_y = intersection.y() - screen_geom.y()
        local_w = intersection.width()
        local_h = intersection.height()

        pixmap = screen.grabWindow(0, local_x, local_y, local_w, local_h)
        if pixmap.isNull():
            continue

        target_x = intersection.x() - global_rect.x()
        target_y = intersection.y() - global_rect.y()
        painter.drawPixmap(target_x, target_y, pixmap)
        captured_any = True
    painter.end()
    if not captured_any:
        return QImage()
    return image


class ScreenCaptureOverlay(QWidget):
    """Оверлей выделения области: Ё → drag → захват."""

    region_captured = pyqtSignal(QImage, QRect)
    cancelled = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._origin: QPoint | None = None
        self._current: QPoint | None = None
        self._selecting = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def show_overlay(self) -> None:
        """Показывает оверлей на всём виртуальном рабочем столе."""
        self._origin = None
        self._current = None
        self._selecting = False
        self.setGeometry(virtual_desktop_geometry())
        QApplication.setOverrideCursor(Qt.CursorShape.CrossCursor)
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus()

    def dismiss(self) -> None:
        """Скрывает оверлей и восстанавливает курсор (в т.ч. при выходе из приложения)."""
        self._hide_overlay()

    def _hide_overlay(self) -> None:
        if QApplication.overrideCursor() is not None:
            QApplication.restoreOverrideCursor()
        self.hide()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self._hide_overlay()
            self.cancelled.emit()
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        self._origin = event.globalPosition().toPoint()
        self._current = self._origin
        self._selecting = True
        self.update()

    def mouseMoveEvent(self, event) -> None:
        if not self._selecting:
            return
        self._current = event.globalPosition().toPoint()
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton or not self._selecting:
            return

        self._selecting = False
        end = event.globalPosition().toPoint()
        selection = normalize_rect(self._origin or end, end)

        self._origin = None
        self._current = None
        self.update()

        if (
            selection.width() < MIN_SELECTION_SIZE
            or selection.height() < MIN_SELECTION_SIZE
        ):
            self._hide_overlay()
            self.cancelled.emit()
            return

        image = capture_region(selection)
        self._hide_overlay()
        if image.isNull():
            self.cancelled.emit()
            return
        self.region_captured.emit(image, selection)

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        overlay_color = QColor(0, 0, 0, 90)
        full_rect = self.rect()

        if self._origin is None or self._current is None:
            painter.fillRect(full_rect, overlay_color)
            return

        desktop = virtual_desktop_geometry()
        selection = normalize_rect(self._origin, self._current)
        local_rect = QRect(
            selection.x() - desktop.x(),
            selection.y() - desktop.y(),
            selection.width(),
            selection.height(),
        )

        # Затемнение вокруг выделения. QRect.bottom()/right() включительные —
        # нижняя/правая полосы начинаем с +1, иначе линия через весь экран.
        if local_rect.top() > full_rect.top():
            painter.fillRect(
                QRect(
                    full_rect.left(),
                    full_rect.top(),
                    full_rect.width(),
                    local_rect.top() - full_rect.top(),
                ),
                overlay_color,
            )

        bottom_y = local_rect.bottom() + 1
        if bottom_y <= full_rect.bottom():
            painter.fillRect(
                QRect(
                    full_rect.left(),
                    bottom_y,
                    full_rect.width(),
                    full_rect.bottom() - bottom_y + 1,
                ),
                overlay_color,
            )

        if local_rect.left() > full_rect.left():
            painter.fillRect(
                QRect(
                    full_rect.left(),
                    local_rect.top(),
                    local_rect.left() - full_rect.left(),
                    local_rect.height(),
                ),
                overlay_color,
            )

        right_x = local_rect.right() + 1
        if right_x <= full_rect.right():
            painter.fillRect(
                QRect(
                    right_x,
                    local_rect.top(),
                    full_rect.right() - right_x + 1,
                    local_rect.height(),
                ),
                overlay_color,
            )

        pen = QPen(QColor(255, 255, 255), 1, Qt.PenStyle.DashLine)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(local_rect)
