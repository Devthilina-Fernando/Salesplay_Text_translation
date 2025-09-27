from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from config.database import get_db
from controllers.excel_export import excel_export

router = APIRouter()

@router.get("/export")
async def export_language_strings(db: Session = Depends(get_db)):
    """
    Export language strings endpoint
    """
    try:
        return await excel_export(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))