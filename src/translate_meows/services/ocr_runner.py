"""Постоянный фоновый поток для OCR (без create/destroy QThread)."""

from typing import Optional

from PyQt6.QtCore import QObject, QThread, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QImage

from translate_meows.services.ocr import recognize_image


class OcrWorker(QObject):
    """Воркер OCR, живёт на постоянном QThread."""

    ocr_requested = pyqtSignal(object, int)
    finished = pyqtSignal(str, int)
    error = pyqtSignal(str, int)

    @pyqtSlot(object, int)
    def run(self, image: QImage, request_id: int) -> None:
        try:
            text = recognize_image(image)
            self.finished.emit(text, request_id)
        except Exception as exc:
            self.error.emit(f"Ошибка распознавания: {exc}", request_id)


class OcrRunner(QObject):
    """Один QThread на всё время жизни приложения."""

    finished = pyqtSignal(str, int)
    error = pyqtSignal(str, int)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._thread = QThread(parent)
        self._worker = OcrWorker()
        self._worker.moveToThread(self._thread)

        self._worker.finished.connect(self.finished)
        self._worker.error.connect(self.error)
        self._worker.ocr_requested.connect(
            self._worker.run, Qt.ConnectionType.QueuedConnection
        )

        self._thread.start()

    def submit(self, image: QImage, request_id: int) -> None:
        self._worker.ocr_requested.emit(image, request_id)

    def shutdown(self, timeout_ms: int = 5000) -> None:
        if not self._thread.isRunning():
            return
        self._thread.quit()
        self._thread.wait(timeout_ms)
