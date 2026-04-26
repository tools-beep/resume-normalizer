from __future__ import annotations

import hmac

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.auth.service import create_api_key, list_api_keys, revoke_api_key
from app.database import get_db
from app.dependencies import get_settings
from app.config import Settings
from app.schemas.auth import APIKeyCreate, APIKeyCreatedResponse, APIKeyResponse

router = APIRouter(tags=["keys"])

admin_key_header = APIKeyHeader(name="X-Admin-Key", scheme_name="AdminKey", auto_error=False)


def require_admin(
    admin_key: str | None = Security(admin_key_header),
    settings: Settings = Depends(get_settings),
) -> None:
    """Verify the admin API key."""
    if admin_key is None:
        raise HTTPException(status_code=401, detail="Missing admin key")
    if not hmac.compare_digest(admin_key, settings.ADMIN_API_KEY.get_secret_value()):
        raise HTTPException(status_code=403, detail="Invalid admin key")


@router.post("/keys", response_model=APIKeyCreatedResponse, dependencies=[Depends(require_admin)])
def create_key(
    body: APIKeyCreate,
    db: Session = Depends(get_db),
) -> APIKeyCreatedResponse:
    """Create a new API key. The raw key is returned only once."""
    key_record, raw_key = create_api_key(db, body.name, body.rate_limit)
    return APIKeyCreatedResponse(
        key=raw_key,
        key_info=APIKeyResponse.model_validate(key_record),
    )


@router.get("/keys", response_model=list[APIKeyResponse], dependencies=[Depends(require_admin)])
def list_keys(
    db: Session = Depends(get_db),
) -> list[APIKeyResponse]:
    """List all API keys (hashes not exposed)."""
    keys = list_api_keys(db)
    return [APIKeyResponse.model_validate(k) for k in keys]


@router.delete("/keys/{key_id}", dependencies=[Depends(require_admin)])
def delete_key(
    key_id: int,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Revoke an API key by ID."""
    if not revoke_api_key(db, key_id):
        raise HTTPException(status_code=404, detail="API key not found")
    return {"status": "revoked"}
