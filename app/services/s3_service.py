from __future__ import annotations

import uuid
from pathlib import PurePosixPath

import boto3
from botocore.exceptions import ClientError

from app.utils.exceptions import S3Error
from app.utils.logging import get_logger

logger = get_logger(__name__)


class S3Service:
    def __init__(
        self,
        region: str,
        bucket_uploads: str,
        bucket_generated: str,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        presigned_url_expiry: int = 3600,
        endpoint_url: str | None = None,
        external_url: str | None = None,
    ):
        self.bucket_uploads = bucket_uploads
        self.bucket_generated = bucket_generated
        self.presigned_url_expiry = presigned_url_expiry
        self._endpoint_url = endpoint_url
        self._external_url = external_url

        client_kwargs: dict = {
            "service_name": "s3",
            "region_name": region,
        }
        # Explicit credentials (local dev / LocalStack). If omitted, boto3
        # falls back to instance role, env vars, or ~/.aws/credentials.
        if aws_access_key_id and aws_secret_access_key:
            client_kwargs["aws_access_key_id"] = aws_access_key_id
            client_kwargs["aws_secret_access_key"] = aws_secret_access_key
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url

        self.client = boto3.client(**client_kwargs)

    def upload_original(
        self,
        file_content: bytes,
        filename: str,
        content_type: str,
    ) -> str:
        """Upload the original resume file to S3. Returns the S3 key."""
        file_uuid = str(uuid.uuid4())
        key = f"originals/{file_uuid}/{filename}"
        return self._upload(self.bucket_uploads, key, file_content, content_type, filename)

    def upload_generated_pdf(
        self,
        pdf_bytes: bytes,
        candidate_name: str,
    ) -> str:
        """Upload the generated standardized PDF to S3. Returns the S3 key."""
        download_name = f"{candidate_name} - Resume.pdf"
        file_uuid = str(uuid.uuid4())
        key = f"generated/{file_uuid}/{download_name}"
        return self._upload(
            self.bucket_generated, key, pdf_bytes, "application/pdf", download_name
        )

    def generate_presigned_url(self, bucket: str, key: str) -> str:
        """Generate a presigned GET URL for an S3 object."""
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=self.presigned_url_expiry,
            )
            # Rewrite internal Docker hostname to external URL for clients
            if self._external_url and self._endpoint_url:
                url = url.replace(self._endpoint_url, self._external_url, 1)
            return url
        except ClientError as e:
            raise S3Error(f"Failed to generate presigned URL: {e}") from e

    def check_connectivity(self) -> bool:
        """Check S3 connectivity by listing buckets."""
        try:
            self.client.list_buckets()
            return True
        except ClientError:
            return False

    def _upload(
        self,
        bucket: str,
        key: str,
        content: bytes,
        content_type: str,
        download_filename: str,
    ) -> str:
        """Upload bytes to an S3 bucket."""
        try:
            self.client.put_object(
                Bucket=bucket,
                Key=key,
                Body=content,
                ContentType=content_type,
                ContentDisposition=f'attachment; filename="{download_filename}"',
            )
            logger.info(
                "S3 upload complete",
                extra={"bucket": bucket, "key": key, "size_bytes": len(content)},
            )
            return key
        except ClientError as e:
            raise S3Error(f"S3 upload failed for {key}: {e}") from e
