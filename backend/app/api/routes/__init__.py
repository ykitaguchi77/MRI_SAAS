from fastapi import APIRouter

from .health import router as health_router
from .upload import router as upload_router
from .segmentation import router as segmentation_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["health"])
api_router.include_router(upload_router, tags=["upload"])
api_router.include_router(segmentation_router, tags=["segmentation"])
