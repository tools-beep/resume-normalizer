from __future__ import annotations

from pydantic import BaseModel

from app.schemas.resume import ResumeData


class ExtractResponse(BaseModel):
    request_id: str
    status: str = "success"
    resume_data: ResumeData
    raw_text: str
    original_file_url: str
    generated_pdf_url: str
    processing_time_ms: float


class ErrorResponse(BaseModel):
    request_id: str
    error: str
    detail: str | None = None


class HealthResponse(BaseModel):
    status: str
    version: str
    services: dict[str, str]
