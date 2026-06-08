"""Постоянный фоновый поток для переводов (без create/destroy QThread)."""

from typing import Optional

from PyQt6.QtCore import QObject, QThread, Qt, pyqtSignal, pyqtSlot

from translate_meows.services.translator import TranslateWorker


class TranslationRunner(QObject):
    """
    Один QThread на всё время жизни приложения.
    Новые запросы ставятся в очередь; устаревшие отбрасываются по request_id в UI.
    """

    finished = pyqtSignal(str, int)
    error = pyqtSignal(str, int)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._thread = QThread(parent)
        self._worker = TranslateWorker()
        self._worker.moveToThread(self._thread)

        self._worker.finished.connect(self.finished)
        self._worker.error.connect(self.error)
        self._worker.translate_requested.connect(
            self._worker.run, Qt.ConnectionType.QueuedConnection
        )

        self._thread.start()

    def submit(
        self,
        text: str,
        request_id: int,
        source: Optional[str],
        target: Optional[str],
    ) -> None:
        self._worker.translate_requested.emit(text, request_id, source, target)

    def shutdown(self, timeout_ms: int = 5000) -> None:
        if not self._thread.isRunning():
            return
        self._thread.quit()
        self._thread.wait(timeout_ms)
