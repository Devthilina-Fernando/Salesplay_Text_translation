"""
Excel import API routes.

This module defines endpoints for importing translations from Excel files.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from config.database import get_db
from controllers.import_excel_strings import import_excel_strings

router = APIRouter(tags=["import"])


@router.post(
    "/excel-import/{language}",
    status_code=status.HTTP_200_OK,
    summary="Import translations from Excel",
    description="Import translated strings from Excel file and update database",
)
async def import_excel_strings_endpoint(
    language: str,
    file: UploadFile = File(..., description="Excel file with translations"),
    db: Session = Depends(get_db),
) -> dict:
    """
    Import translations from Excel file.
    
    The Excel file must contain:
    - msgid column: Message IDs
    - msgstr column: Translated strings
    
    Only rows with non-empty msgstr values will be processed.
    
    Args:
        language: Target language name.
        file: Uploaded Excel file (.xlsx or .xls).
        db: Database session (injected).
        
    Returns:
        Dictionary with import statistics.
        
    Raises:
        HTTPException: If validation fails or import errors occur.
    """
    try:
        result = await import_excel_strings(language, db, file)
        return result

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))