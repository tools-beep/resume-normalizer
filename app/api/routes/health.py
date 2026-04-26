from importlib.metadata import version

from fastapi import APIRouter, Depends

from app.dependencies import get_s3_service
from app.schemas.response import HealthResponse
from app.services.s3_service import S3Service

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check(
    s3_service: S3Service = Depends(get_s3_service),
) -> HealthResponse:
    """Check service health and connectivity."""
    try:
        app_version = version("resume-normalizer")
    except Exception:
        app_version = "0.1.0"

    s3_status = "connected" if s3_service.check_connectivity() else "disconnected"

    return HealthResponse(
        status="healthy",
        version=app_version,
        services={
            "s3": s3_status,
        },
    )
