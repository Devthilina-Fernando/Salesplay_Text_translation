from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from config.database import get_db
from controllers.import_excel_strings import import_excel_strings

router = APIRouter()

@router.post("/excel-import/{language}")
async def import_excel_strings_endpoint(
    language: str, 
    db: Session = Depends(get_db), 
    file: UploadFile = File(...)
):
    """
    Import Excel file with language strings endpoint
    """
    try:
        return await import_excel_strings(language, db, file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))