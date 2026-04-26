from __future__ import annotations

from functools import lru_cache

from fastapi import Depends

from app.config import Settings
from app.services.llm_service import LLMService
from app.services.pipeline import Pipeline
from app.services.s3_service import S3Service


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_s3_service(settings: Settings = Depends(get_settings)) -> S3Service:
    return S3Service(
        region=settings.AWS_REGION,
        bucket_uploads=settings.S3_BUCKET_UPLOADS,
        bucket_generated=settings.S3_BUCKET_GENERATED,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=(
            settings.AWS_SECRET_ACCESS_KEY.get_secret_value()
            if settings.AWS_SECRET_ACCESS_KEY
            else None
        ),
        presigned_url_expiry=settings.S3_PRESIGNED_URL_EXPIRY,
        endpoint_url=settings.AWS_ENDPOINT_URL,
        external_url=settings.S3_EXTERNAL_URL,
    )


def get_llm_service(settings: Settings = Depends(get_settings)) -> LLMService:
    return LLMService(
        api_key=settings.OPENAI_API_KEY.get_secret_value(),
        model=settings.OPENAI_MODEL,
        max_retries=settings.OPENAI_MAX_RETRIES,
        temperature=settings.OPENAI_TEMPERATURE,
    )


def get_pipeline(
    settings: Settings = Depends(get_settings),
    s3_service: S3Service = Depends(get_s3_service),
    llm_service: LLMService = Depends(get_llm_service),
) -> Pipeline:
    return Pipeline(settings=settings, s3_service=s3_service, llm_service=llm_service)
