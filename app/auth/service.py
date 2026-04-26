from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.auth.models import APIKey
from app.utils.logging import get_logger

logger = get_logger(__name__)

KEY_PREFIX = "rn_live_"


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def create_api_key(db: Session, name: str, rate_limit: int | None = None) -> tuple[APIKey, str]:
    """Create a new API key. Returns the DB record and the raw key (shown once)."""
    raw_key = f"{KEY_PREFIX}{secrets.token_hex(32)}"
    key_hash = _hash_key(raw_key)

    api_key = APIKey(
        key_hash=key_hash,
        name=name,
        rate_limit=rate_limit,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    logger.info("API key created", extra={"key_id": api_key.id, "key_name": name})
    return api_key, raw_key


def validate_api_key(db: Session, raw_key: str) -> APIKey | None:
    """Validate an API key and update usage stats. Returns None if invalid."""
    key_hash = _hash_key(raw_key)
    api_key = db.query(APIKey).filter(APIKey.key_hash == key_hash).first()

    if api_key is None:
        return None

    if not api_key.is_active:
        return None

    api_key.last_used_at = datetime.now(timezone.utc)
    api_key.request_count += 1
    db.commit()

    return api_key


def list_api_keys(db: Session) -> list[APIKey]:
    """List all API keys (without exposing hashes)."""
    return db.query(APIKey).order_by(APIKey.created_at.desc()).all()


def revoke_api_key(db: Session, key_id: int) -> bool:
    """Revoke an API key by ID. Returns True if found and revoked."""
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if api_key is None:
        return False

    api_key.is_active = False
    db.commit()

    logger.info("API key revoked", extra={"key_id": key_id})
    return True
