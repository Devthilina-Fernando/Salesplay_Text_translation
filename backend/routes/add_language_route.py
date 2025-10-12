"""
Add language API routes.

This module defines endpoints for adding new language locales to the system.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from config.database import get_db
from config.logger import logger
from controllers.add_language import add_language_locale
from schemas.translation import LanguageLocaleCreate

router = APIRouter(tags=["languages"])


@router.post(
    "/add-language",
    status_code=status.HTTP_201_CREATED,
    summary="Add new language",
    description="Add a new language locale and create translation column",
    responses={
        201: {"description": "Language added successfully"},
        400: {"description": "Validation error or duplicate language"},
        500: {"description": "Server error"},
    },
)
async def add_language_endpoint(
    locale_data: LanguageLocaleCreate, db: Session = Depends(get_db)
) -> dict:
    """
    Add a new language locale to the system.
    
    This operation:
    1. Creates a new language locale record
    2. Adds a corresponding column to the language_strings table
    3. Both operations are transactional (all or nothing)
    
    Args:
        locale_data: Language locale creation data.
        db: Database session (injected).
        
    Returns:
        Dictionary with locale ID and language code.
        
    Raises:
        HTTPException: If validation fails or language already exists.
    """
    try:
        result = add_language_locale(db, locale_data)
        
        logger.info(
            "Language locale added successfully",
            extra={
                "locale_id": result["id"],
                "language_code": result["language_code"],
            },
        )
        
        return {
            "message": "Language locale and column added successfully",
            "locale_id": result["id"],
            "new_column": result["language_code"],
        }

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except RuntimeError as e:
        logger.error(f"Operation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500, detail="An unexpected error occurred"
        )