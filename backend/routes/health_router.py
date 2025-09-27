from fastapi import APIRouter, status
from config.logger import logger
from pydantic import BaseModel
from schemas.translation import HealthStatus

router = APIRouter()

# Basic health check endpoint
@router.get(
    "/health",
    response_model=HealthStatus,
    status_code=status.HTTP_200_OK,
    tags=["Health"],
    summary="Basic Health Check",
    description="Returns basic health status of the API"
)
async def health_check():
    """
    Basic health check endpoint that returns minimal information.
    Used by frontend to check API connectivity.
    """
    
    return HealthStatus(
        status="healthy"
    )