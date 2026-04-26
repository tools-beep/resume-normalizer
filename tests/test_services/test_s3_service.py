import boto3
import pytest
from moto import mock_aws

from app.services.s3_service import S3Service


@pytest.fixture
def s3_service():
    """S3Service with mocked AWS."""
    with mock_aws():
        # Create buckets
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="test-uploads")
        client.create_bucket(Bucket="test-generated")

        service = S3Service(
            aws_access_key_id="testing",
            aws_secret_access_key="testing",
            region="us-east-1",
            bucket_uploads="test-uploads",
            bucket_generated="test-generated",
        )
        yield service


def test_upload_original(s3_service):
    """Uploading an original file returns a valid S3 key."""
    key = s3_service.upload_original(b"pdf content", "resume.pdf", "application/pdf")
    assert key.startswith("originals/")
    assert key.endswith("/resume.pdf")


def test_upload_generated_pdf(s3_service):
    """Uploading a generated PDF returns a key with candidate name."""
    key = s3_service.upload_generated_pdf(b"%PDF-1.4...", "Jane Smith")
    assert key.startswith("generated/")
    assert key.endswith("/Jane Smith - Resume.pdf")


def test_generate_presigned_url(s3_service):
    """Presigned URLs are generated for uploaded objects."""
    s3_service.upload_original(b"content", "test.pdf", "application/pdf")
    # Just verify it doesn't raise — URL format varies with moto
    url = s3_service.generate_presigned_url("test-uploads", "originals/fake/test.pdf")
    assert isinstance(url, str)
    assert len(url) > 0


def test_check_connectivity(s3_service):
    """Connectivity check returns True when S3 is accessible."""
    assert s3_service.check_connectivity() is True
