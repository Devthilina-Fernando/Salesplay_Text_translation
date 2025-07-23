from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
from config.database import get_db
from config.logger import logger
from config.config import Config
from schemas.translation import LanguageLocaleCreate
from controllers.add_language import add_language_locale

router = APIRouter()

@router.post("/add-language")
async def add_language_endpoint(
    locale_data: LanguageLocaleCreate,
    db: Session = Depends(get_db)
):
    try:
        print("///////////////////////////////")
        print(locale_data)
        result = add_language_locale(db, locale_data)
        return {
            "message": "Language locale and column added successfully",
            "locale_id": result["id"],  # Access dictionary key
            "new_column": result["language_code"]
        }
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Operation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))