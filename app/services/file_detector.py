from __future__ import annotations

from enum import Enum

from app.utils.exceptions import FileValidationError
from app.utils.logging import get_logger

logger = get_logger(__name__)


class FileType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    IMAGE = "image"


_MIME_MAP: dict[str, FileType] = {
    "application/pdf": FileType.PDF,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": FileType.DOCX,
    "image/png": FileType.IMAGE,
    "image/jpeg": FileType.IMAGE,
}

_EXT_MAP: dict[str, FileType] = {
    ".pdf": FileType.PDF,
    ".docx": FileType.DOCX,
    ".png": FileType.IMAGE,
    ".jpg": FileType.IMAGE,
    ".jpeg": FileType.IMAGE,
}


def _detect_mime(file_content: bytes) -> str | None:
    """Detect MIME type using libmagic. Returns None if libmagic is unavailable."""
    try:
        import magic
        return magic.from_buffer(file_content[:2048], mime=True)
    except ImportError:
        logger.warning("libmagic not available, using extension-only detection")
        return None


def detect_file_type(
    file_content: bytes,
    filename: str,
    allowed_mime_types: list[str],
) -> FileType:
    """Detect file type from content bytes using libmagic, with extension fallback."""
    mime_type = _detect_mime(file_content)
    logger.info("File type detection", extra={"file_name": filename, "mime_type": mime_type})

    if mime_type and mime_type in _MIME_MAP:
        if mime_type not in allowed_mime_types:
            raise FileValidationError(
                f"File type '{mime_type}' is not allowed. "
                f"Allowed types: {', '.join(allowed_mime_types)}"
            )
        return _MIME_MAP[mime_type]

    # Extension fallback (also used when libmagic is unavailable)
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in _EXT_MAP:
        file_type = _EXT_MAP[ext]
        if not mime_type:
            logger.info(
                "Using extension-based detection",
                extra={"file_name": filename, "extension": ext},
            )
        else:
            logger.warning(
                "MIME detection inconclusive, using extension fallback",
                extra={"file_name": filename, "mime_type": mime_type, "extension": ext},
            )
        return file_type

    raise FileValidationError(
        f"Unsupported file type '{mime_type or 'unknown'}' for file '{filename}'. "
        f"Allowed types: {', '.join(allowed_mime_types)}"
    )
