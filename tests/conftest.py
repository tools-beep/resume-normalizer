from __future__ import annotations

import os
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.auth.service import create_api_key
from app.config import Settings
from app.database import Base, get_db
from app.dependencies import get_settings

TEST_ADMIN_KEY = "test-admin-key"
TEST_DB_URL = "sqlite:///./test_api_keys.db"


def _make_test_settings() -> Settings:
    return Settings(
        APP_ENV="test",
        LOG_LEVEL="WARNING",
        OPENAI_API_KEY="sk-test-key",
        OPENAI_MODEL="gpt-4.1-mini",
        AWS_ACCESS_KEY_ID="testing",
        AWS_SECRET_ACCESS_KEY="testing",
        AWS_REGION="us-east-1",
        S3_BUCKET_UPLOADS="test-uploads",
        S3_BUCKET_GENERATED="test-generated",
        DATABASE_URL=TEST_DB_URL,
        ADMIN_API_KEY=TEST_ADMIN_KEY,
    )


@pytest.fixture
def test_settings() -> Settings:
    return _make_test_settings()


@pytest.fixture
def test_db(test_settings: Settings) -> Generator[Session, None, None]:
    engine = create_engine(
        test_settings.DATABASE_URL, connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        db_path = test_settings.DATABASE_URL.replace("sqlite:///", "")
        if os.path.exists(db_path):
            os.remove(db_path)


@pytest.fixture
def test_api_key(test_db: Session) -> str:
    """Create a test API key and return the raw key."""
    _, raw_key = create_api_key(test_db, "test-client")
    return raw_key


@pytest.fixture
def s3_mock():
    """Provide mocked S3 via moto."""
    with mock_aws():
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="test-uploads")
        client.create_bucket(Bucket="test-generated")
        yield client


@pytest.fixture
def mock_openai_response():
    """Return a mock OpenAI parsed response."""
    from app.schemas.resume import PersonalInfo, ResumeData

    return ResumeData(
        personal_info=PersonalInfo(
            full_name="Jane Smith",
            email="jane@example.com",
            phone="+1-555-0123",
            city="San Francisco",
            country="USA",
        ),
        summary="Experienced software engineer",
        skills=["Python", "FastAPI", "AWS"],
    )


@pytest.fixture
def client(test_settings: Settings, test_db: Session) -> Generator[TestClient, None, None]:
    """FastAPI test client with overridden dependencies."""
    from app.main import app

    # Clear the lru_cache so lifespan picks up the test settings
    get_settings.cache_clear()

    def override_settings() -> Settings:
        return test_settings

    def override_db() -> Generator[Session, None, None]:
        yield test_db

    app.dependency_overrides[get_settings] = override_settings
    app.dependency_overrides[get_db] = override_db

    # Patch get_settings in the main module so lifespan uses test settings
    with patch("app.main.get_settings", return_value=test_settings):
        with TestClient(app) as c:
            yield c

    app.dependency_overrides.clear()
    get_settings.cache_clear()
