from fastapi import APIRouter

from app.api.v1.endpoints import health, ingestion, ready

api_router = APIRouter()
api_router.include_router(health.router, tags=["System Health"])
api_router.include_router(ready.router, tags=["System Health"])
api_router.include_router(ingestion.router)
