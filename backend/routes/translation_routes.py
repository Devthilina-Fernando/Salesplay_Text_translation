"""
Translation API routes.

This module defines API endpoints for translation operations including
PO file generation and translation uploads.
"""

import os
from csv import reader
from io import StringIO

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from config.config import Config
from config.database import get_db
from config.logger import logger
from controllers.translation_controller import (
    extract_translations_from_rows,
    generate_po_content,
    get_language_code_by_name,
    get_zero_msgids,
    process_uploaded_translations,
    read_csv_file,
    read_excel_file,
    translate_msgids,
    update_po_content,
)

router = APIRouter(tags=["translations"])


@router.post(
    "/generate-po/{language}",
    status_code=status.HTTP_200_OK,
    summary="Generate PO file",
    description="Generate PO file for a language by translating untranslated strings",
)
async def generate_po_endpoint(
    language: str, db: Session = Depends(get_db)
) -> dict:
    """
    Generate PO file for specified language.
    
    This endpoint:
    1. Finds all untranslated message IDs for the language
    2. Translates them using OpenAI
    3. Creates or updates the PO file
    
    Args:
        language: Target language name (e.g., "Spanish", "French").
        db: Database session (injected).
        
    Returns:
        Dictionary with operation status and message.
        
    Raises:
        HTTPException: If language not found or operation fails.
    """
    try:
        # Validate language exists
        lang_code = get_language_code_by_name(db, language)
        if not lang_code:
            error_msg = f"Language '{language}' not found"
            logger.error(error_msg)
            raise HTTPException(status_code=404, detail=error_msg)

        # Get untranslated strings
        msgids = get_zero_msgids(db, lang_code)
        if not msgids:
            return {"message": "No translations needed"}

        # Translate strings
        translations = await translate_msgids(db, msgids, language, lang_code)

        # Prepare PO file paths
        po_dir = os.path.join(Config.LOCALES_DIR, lang_code, "LC_MESSAGES")
        os.makedirs(po_dir, exist_ok=True)
        po_path = os.path.join(po_dir, "salesplaypos.po")

        # Create or update PO file
        if os.path.exists(po_path):
            with open(po_path, "r", encoding="utf-8") as f:
                existing_content = f.read()

            updated_content = update_po_content(
                existing_content, language, msgids, translations
            )

            with open(po_path, "w", encoding="utf-8") as f:
                f.write(updated_content)
            action = "updated"
        else:
            po_content = generate_po_content(
                language, lang_code, msgids, translations
            )
            with open(po_path, "w", encoding="utf-8") as f:
                f.write(po_content)
            action = "created"

        logger.info(
            f"PO file {action}",
            extra={"language": language, "translations_count": len(msgids)},
        )

        return {"message": f"PO file {action} for {language}"}

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"PO generation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/upload-translations/{language}",
    status_code=status.HTTP_200_OK,
    summary="Upload translations",
    description="Upload translations from CSV or Excel file",
)
async def upload_translations(
    language: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    """
    Upload translations from file (CSV, XLSX, or XLS).
    
    The file must contain 'msgid' and 'msgstr' columns.
    
    Args:
        language: Target language name.
        file: Uploaded file (CSV or Excel).
        db: Database session (injected).
        
    Returns:
        Dictionary with upload statistics.
        
    Raises:
        HTTPException: If validation fails or operation errors.
    """
    try:
        # Validate language
        lang_code = get_language_code_by_name(db, language)
        if not lang_code:
            error_msg = f"Language '{language}' not found"
            logger.error(error_msg)
            raise HTTPException(status_code=404, detail=error_msg)

        # Get file extension
        filename = file.filename.lower()
        if "." not in filename:
            raise HTTPException(
                status_code=400, detail="File has no extension"
            )

        ext = filename.rsplit(".", 1)[1]

        # Read file content
        content = await file.read()

        # Process based on file type
        if ext == "csv":
            decoded_content = read_csv_file(content)
            csv_file = StringIO(decoded_content)
            csv_reader = reader(csv_file)
            rows = list(csv_reader)
            msgids, translations = extract_translations_from_rows(rows)

        elif ext in ["xlsx", "xls"]:
            rows = read_excel_file(content, ext)
            msgids, translations = extract_translations_from_rows(rows)

        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Use CSV, XLSX, or XLS",
            )

        # Validate translations exist
        if not msgids:
            raise HTTPException(
                status_code=400, detail="No translations found in file"
            )

        # Update database
        process_uploaded_translations(db, lang_code, msgids, translations)

        # Generate PO file
        po_dir = os.path.join(Config.LOCALES_DIR, lang_code, "LC_MESSAGES")
        os.makedirs(po_dir, exist_ok=True)
        po_path = os.path.join(po_dir, "salesplaypos.po")

        po_content = generate_po_content(language, lang_code, msgids, translations)

        with open(po_path, "w", encoding="utf-8") as f:
            f.write(po_content)

        logger.info(
            "Translations uploaded successfully",
            extra={
                "language": language,
                "translations_processed": len(msgids),
            },
        )

        return {
            "message": f"Translations uploaded successfully for {language}",
            "translations_processed": len(msgids),
            "po_file_path": po_path,
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.exception(f"Translation upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))