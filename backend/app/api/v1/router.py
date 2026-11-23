from fastapi import APIRouter

from app.api.v1.endpoints import health, ingestion, memory, ready, retrieval

api_router = APIRouter()
api_router.include_router(health.router, tags=["System Health"])
api_router.include_router(ready.router, tags=["System Health"])
api_router.include_router(ingestion.router)
api_router.include_router(memory.router)
api_router.include_router(retrieval.router)
