from __future__ import annotations

import pytesseract
from pdf2image import convert_from_bytes

from app.utils.exceptions import OCRError
from app.utils.logging import get_logger

logger = get_logger(__name__)


def configure_tesseract(tesseract_cmd: str) -> None:
    """Set the Tesseract binary path."""
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd


def ocr_from_pdf(file_content: bytes) -> str:
    """Convert PDF pages to images and run OCR on each."""
    try:
        images = convert_from_bytes(file_content)
        logger.info("PDF converted to images for OCR", extra={"page_count": len(images)})

        text_parts: list[str] = []
        for i, img in enumerate(images):
            page_text = pytesseract.image_to_string(img)
            text_parts.append(page_text)
            logger.debug(
                "OCR page complete",
                extra={"page": i + 1, "chars": len(page_text)},
            )

        result = "\n".join(text_parts)
        logger.info("PDF OCR complete", extra={"total_chars": len(result)})
        return result
    except OCRError:
        raise
    except Exception as e:
        raise OCRError(f"OCR failed on PDF: {e}") from e
