from fastapi import APIRouter , Depends, HTTPException, status
from controllers.get_languages import get_all_languages
from config.database import get_db
from sqlalchemy.orm import Session
from config.logger import logger
from typing import List

router = APIRouter()


@router.get("/get_all_languages", response_model=List[str])
def read_languages(db: Session = Depends(get_db)) -> List[str]:

    # Retrieve all unique language codes from the language_locales table.
    try:
        languages = get_all_languages(db)
        # Ensure result is a list of strings
        if not isinstance(languages, list):
            raise ValueError("Invalid return type from get_all_languages, expected list[str]")
        return languages

    except HTTPException:
        # Re-raise HTTP exceptions to
        raise
    except Exception as exc:
        logger.error("Error fetching languages: %s", exc, exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving languages."
        )