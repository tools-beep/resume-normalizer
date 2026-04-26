import pytest

from app.services.file_detector import FileType, detect_file_type
from app.utils.exceptions import FileValidationError

ALLOWED = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/png",
    "image/jpeg",
]


def test_detect_pdf():
    """PDF magic bytes are correctly detected."""
    pdf_header = b"%PDF-1.4 " + b"\x00" * 100
    result = detect_file_type(pdf_header, "resume.pdf", ALLOWED)
    assert result == FileType.PDF


def test_detect_png():
    """PNG magic bytes are correctly detected."""
    png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    result = detect_file_type(png_header, "resume.png", ALLOWED)
    assert result == FileType.IMAGE


def test_detect_jpeg():
    """JPEG magic bytes are correctly detected."""
    jpeg_header = b"\xff\xd8\xff\xe0" + b"\x00" * 100
    result = detect_file_type(jpeg_header, "resume.jpg", ALLOWED)
    assert result == FileType.IMAGE


def test_unsupported_type_raises():
    """Unsupported file types raise FileValidationError."""
    with pytest.raises(FileValidationError):
        detect_file_type(b"plain text content", "resume.txt", ALLOWED)
