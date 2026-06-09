"""Распознавание текста через встроенный Windows OCR."""

from typing import Any

from PIL import Image
from PyQt6.QtGui import QImage

import winocr

OCR_LANG = "en"


def qimage_to_pil(image: QImage) -> Image.Image:
    """Конвертирует QImage в PIL.Image для winocr (без QImage.save в BytesIO)."""
    converted = image.convertToFormat(QImage.Format.Format_RGBA8888)
    width = converted.width()
    height = converted.height()
    if width <= 0 or height <= 0:
        raise ValueError("Пустое изображение для OCR")

    bytes_per_line = converted.bytesPerLine()
    ptr = converted.bits()
    ptr.setsize(converted.sizeInBytes())
    raw = bytes(ptr)

    pixel_width = width * 4
    if bytes_per_line == pixel_width:
        return Image.frombytes("RGBA", (width, height), raw)

    rows = [
        raw[y * bytes_per_line : y * bytes_per_line + pixel_width]
        for y in range(height)
    ]
    return Image.frombytes("RGBA", (width, height), b"".join(rows))


def extract_text(result: dict[str, Any]) -> str:
    """Достаёт распознанный текст из ответа winocr."""
    text = (result.get("text") or "").strip()
    if text:
        return text

    lines: list[str] = []
    for line in result.get("lines", []):
        if isinstance(line, dict):
            line_text = (line.get("text") or "").strip()
            if line_text:
                lines.append(line_text)
    return "\n".join(lines).strip()


def friendly_ocr_error(exc: Exception) -> str:
    """Преобразует ошибку OCR в понятное сообщение."""
    message = str(exc).lower()
    if "language" in message or "ocr" in message or "assertion" in message:
        return (
            "OCR-пакет языка не установлен в Windows. "
            "Проверьте Language.OCR в параметрах системы."
        )
    return f"Ошибка распознавания: {exc}"


def recognize_image(image: QImage) -> str:
    """Распознаёт текст на изображении (только EN OCR)."""
    pil_image = qimage_to_pil(image)
    try:
        result = winocr.recognize_pil_sync(pil_image, OCR_LANG)
    except Exception as exc:
        raise RuntimeError(friendly_ocr_error(exc)) from exc
    return extract_text(result)
