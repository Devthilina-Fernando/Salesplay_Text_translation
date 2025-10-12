"""
Health check API routes.

This module defines endpoints for application health monitoring.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from config.config import Config
from config.database import get_db
from config.logger import logger

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check application and database health",
)
async def health_check(db: Session = Depends(get_db)) -> dict:
    """
    Perform application health check.
    
    Checks:
    - Application status
    - Database connectivity
    - Current timestamp
    
    Args:
        db: Database session (injected).
        
    Returns:
        Dictionary with health status.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": Config.ENVIRONMENT if hasattr(Config, 'ENVIRONMENT') else "unknown",
    }

    # Check database connectivity
    try:
        db.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        health_status["status"] = "unhealthy"
        health_status["database"] = "disconnected"
        health_status["error"] = str(e)

    return health_status


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness check",
    description="Check if application is ready to serve requests",
)
async def readiness_check() -> dict:
    """
    Check if application is ready.
    
    Returns:
        Dictionary with readiness status.
    """
    return {
        "ready": True,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get(
    "/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness check",
    description="Check if application is alive",
)
async def liveness_check() -> dict:
    """
    Check if application is alive.
    
    Returns:
        Dictionary with liveness status.
    """
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat(),
    }