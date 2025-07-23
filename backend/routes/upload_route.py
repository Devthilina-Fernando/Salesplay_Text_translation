from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from controllers.upload_file import handle_file_upload
from controllers.upload_file import insert_new_strings_from_file
from sqlalchemy.orm import Session
from config.database import get_db
from config.logger import logger

router = APIRouter()
    
@router.post("/upload")
async def upload_and_insert_strings(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        await handle_file_upload(file)
        result = insert_new_strings_from_file(db)  

        return {
            "message" : f"Inserted {result["inserted_count"]} new strings",
            "inserted_count": result["inserted_count"],
            "skipped": result["skipped"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload & insert error: {e!r}")
        raise HTTPException(status_code=500, detail="Internal processing error")
    

@router.get("/upload-strings")
async def upload_strings_file(
    db: Session = Depends(get_db)
):
    try:
        count = insert_new_strings_from_file(db)
        return {"message": f"Inserted {count} new strings"}
    
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))