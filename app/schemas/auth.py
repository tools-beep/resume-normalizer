from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class APIKeyCreate(BaseModel):
    name: str
    rate_limit: int | None = None


class APIKeyResponse(BaseModel):
    id: int
    name: str
    is_active: bool
    rate_limit: int | None
    created_at: datetime
    last_used_at: datetime | None
    request_count: int

    model_config = {"from_attributes": True}


class APIKeyCreatedResponse(BaseModel):
    key: str
    key_info: APIKeyResponse
