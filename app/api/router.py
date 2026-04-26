from fastapi import APIRouter

from app.api.routes import extract, health, keys

router = APIRouter(prefix="/api/v1")
router.include_router(health.router)
router.include_router(extract.router)
router.include_router(keys.router)
