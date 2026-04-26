from __future__ import annotations

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def _get_api_key_from_request(request: Request) -> str:
    """Extract API key from request for rate limiting."""
    return request.headers.get("X-API-Key", get_remote_address(request))


limiter = Limiter(key_func=_get_api_key_from_request)
