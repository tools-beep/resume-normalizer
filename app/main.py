from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from app.api.router import router
from app.auth.models import APIKey  # noqa: F401 — ensure model is registered
from app.database import init_db
from app.dependencies import get_settings
from app.rate_limit import limiter
from app.utils.logging import get_logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown."""
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)
    logger = get_logger(__name__)

    # Initialize database
    init_db(settings.DATABASE_URL)
    logger.info("Database initialized")

    # Store rate limit config
    app.state.rate_limit = f"{settings.RATE_LIMIT_PER_MINUTE}/minute"

    logger.info(
        "Application started",
        extra={"env": settings.APP_ENV, "rate_limit": app.state.rate_limit},
    )
    yield
    logger.info("Application shutting down")


app = FastAPI(
    title="Resume Normalizer API",
    description=(
        "API for processing resumes: extracts text from PDF/DOCX/images, "
        "structures data via LLM, and generates standardized PDFs."
    ),
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "health", "description": "Service health checks"},
        {"name": "extract", "description": "Resume extraction and normalization"},
        {"name": "keys", "description": "API key management (admin)"},
    ],
)

# Rate limiter
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    return Response(
        content='{"error": "rate_limit_exceeded", "detail": "Too many requests"}',
        status_code=429,
        media_type="application/json",
    )


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):  # type: ignore[no-untyped-def]
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Routes
app.include_router(router)
