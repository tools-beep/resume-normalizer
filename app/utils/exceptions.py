class FileValidationError(ValueError):
    """Raised when an uploaded file fails validation (type, size)."""


class TextExtractionError(RuntimeError):
    """Raised when text extraction fails after all attempts."""


class OCRError(RuntimeError):
    """Raised when OCR processing fails."""


class LLMExtractionError(RuntimeError):
    """Raised when LLM returns invalid or unparseable data."""


class LLMRetryExhaustedError(LLMExtractionError):
    """Raised when all LLM retry attempts are exhausted."""


class PDFRenderError(RuntimeError):
    """Raised when PDF rendering fails."""


class S3Error(RuntimeError):
    """Raised when S3 operations fail."""
