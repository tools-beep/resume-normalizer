from __future__ import annotations

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.auth.models import APIKey
from app.auth.service import validate_api_key
from app.database import get_db

api_key_header = APIKeyHeader(name="X-API-Key", scheme_name="APIKey", auto_error=False)


def require_api_key(
    request: Request,
    api_key: str | None = Security(api_key_header),
    db: Session = Depends(get_db),
) -> APIKey:
    """Dependency that validates the X-API-Key header and returns the key record."""
    if api_key is None:
        raise HTTPException(status_code=401, detail="Missing API key")

    key_record = validate_api_key(db, api_key)
    if key_record is None:
        raise HTTPException(status_code=401, detail="Invalid or revoked API key")

    # Store on request state for per-key rate limiting
    request.state.api_key_record = key_record
    return key_record
