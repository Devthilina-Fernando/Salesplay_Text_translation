"""
File upload API routes.

This module defines endpoints for uploading text files with language strings.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from config.database import get_db
from config.logger import logger
from controllers.upload_file import (
    handle_file_upload,
    insert_new_strings_from_file,
)

router = APIRouter(tags=["upload"])


@router.post(
    "/upload",
    status_code=status.HTTP_200_OK,
    summary="Upload strings file",
    description="Upload text file and insert new strings into database",
)
async def upload_and_insert_strings(
    file: UploadFile = File(..., description="Text file with strings"),
    db: Session = Depends(get_db),
) -> dict:
    """
    Upload text file and insert new strings.
    
    The file should contain one string per line. Duplicate strings
    (already in database or within the file) will be skipped.
    
    Args:
        file: Uploaded text file.
        db: Database session (injected).
        
    Returns:
        Dictionary with insertion statistics.
        
    Raises:
        HTTPException: If file validation fails or processing errors occur.
    """
    try:
        # Upload file
        await handle_file_upload(file)

        # Process and insert strings
        result = insert_new_strings_from_file(db)

        logger.info(
            "Strings uploaded and inserted",
            extra={
                "inserted_count": result["inserted_count"],
                "skipped_count": len(result["skipped"]),
            },
        )

        return {
            "message": f"Inserted {result['inserted_count']} new strings",
            "inserted_count": result["inserted_count"],
            "skipped": result["skipped"],
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Upload & insert error: {e!r}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal processing error")


@router.get(
    "/upload-strings",
    status_code=status.HTTP_200_OK,
    summary="Process uploaded strings",
    description="Process strings from previously uploaded file",
)
async def upload_strings_file(db: Session = Depends(get_db)) -> dict:
    """
    Process strings from uploaded file.
    
    This endpoint processes the default strings.txt file from the uploads
    directory. The file must have been uploaded previously.
    
    Args:
        db: Database session (injected).
        
    Returns:
        Dictionary with insertion count.
        
    Raises:
        HTTPException: If file not found or processing fails.
    """
    try:
        result = insert_new_strings_from_file(db)

        return {
            "message": f"Inserted {result['inserted_count']} new strings",
            "inserted_count": result["inserted_count"],
        }

    except FileNotFoundError as e:
        logger.error(f"File not found: {str(e)}")
        raise HTTPException(status_code=404, detail="Strings file not found")

    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))