"""
Get languages API routes.

This module defines endpoints for retrieving language information.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from config.database import get_db
from config.logger import logger
from controllers.get_languages import get_all_languages

router = APIRouter(tags=["languages"])


@router.get(
    "/get_all_languages",
    response_model=List[str],
    status_code=status.HTTP_200_OK,
    summary="Get all languages",
    description="Retrieve all unique language names from the system",
)
def read_languages(db: Session = Depends(get_db)) -> List[str]:
    """
    Retrieve all unique language names.
    
    Args:
        db: Database session (injected).
        
    Returns:
        List of language names.
        
    Raises:
        HTTPException: If database query fails.
    """
    try:
        languages = get_all_languages(db)

        # Validate result type
        if not isinstance(languages, list):
            raise ValueError(
                "Invalid return type from get_all_languages, expected list[str]"
            )

        logger.info(f"Retrieved {len(languages)} languages")
        return languages

    except HTTPException:
        raise

    except Exception as exc:
        logger.error("Error fetching languages: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving languages.",
        )