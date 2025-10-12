"""
Excel export API routes.

This module defines endpoints for exporting language strings to Excel.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from config.database import get_db
from controllers.excel_export import excel_export

router = APIRouter(tags=["export"])


@router.get(
    "/export",
    response_class=StreamingResponse,
    summary="Export language strings",
    description="Export all language strings to Excel file with empty msgstr values",
)
async def export_language_strings(
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """
    Export language strings to Excel file.
    
    The exported file contains:
    - msgid column: Original message IDs
    - msgstr column: Empty (for manual translation)
    
    Args:
        db: Database session (injected).
        
    Returns:
        StreamingResponse with Excel file download.
        
    Raises:
        HTTPException: If export operation fails.
    """
    try:
        return await excel_export(db)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))