"""Health check endpoint"""

from fastapi import APIRouter

from app.core.model_loader import get_model_manager
from app.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API and model health"""
    model_manager = get_model_manager()

    return HealthResponse(
        status="healthy",
        model_loaded=model_manager.is_loaded(),
        gpu_available=model_manager.is_gpu_available(),
        device=model_manager.get_device()
    )
