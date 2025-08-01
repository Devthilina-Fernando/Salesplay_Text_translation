from fastapi import APIRouter, Depends, HTTPException, UploadFile, File,status
from sqlalchemy.orm import Session
from config.database import get_db
from config.logger import logger
from controllers.translation_controller import (
    get_zero_msgids,
    translate_msgids,
    generate_po_content,
    get_language_code_by_name,
    update_po_content,
    process_uploaded_translations,read_csv_file,
    read_excel_file,extract_translations_from_rows
)
import os
from config.config import Config
import csv
from io import StringIO

router = APIRouter()
    
@router.post("/generate-po/{language}")
async def generate_po_endpoint(
    language: str,
    db: Session = Depends(get_db)
):
    try:
        lang_code = get_language_code_by_name(db, language)
        if not lang_code:
            error_msg = f"Language '{language}' not found"
            logger.error(error_msg)
            raise HTTPException(status_code=404, detail=error_msg)
        
        msgids = get_zero_msgids(db, lang_code)
        if not msgids:
            return {"message": "No translations needed"}
        
        translations = await translate_msgids(db, msgids, language, lang_code)
        # translations = translate_msgids(db, msgids, language, lang_code)
        po_dir = os.path.join(Config.LOCALES_DIR, lang_code, "LC_MESSAGES")
        os.makedirs(po_dir, exist_ok=True)
        po_path = os.path.join(po_dir, "salesplaypos.po")
        
        # Check if PO file exists
        if os.path.exists(po_path):
            # Update existing PO file
            with open(po_path, "r", encoding="utf-8") as f:
                existing_content = f.read()
            
            # Parse existing content and add new translations
            updated_content = update_po_content(
                existing_content, 
                language, 
                msgids, 
                translations
            )
            
            with open(po_path, "w", encoding="utf-8") as f:
                f.write(updated_content)
            action = "updated"
        else:
            # Create new PO file
            po_content = generate_po_content(language,lang_code, msgids, translations)
            with open(po_path, "w", encoding="utf-8") as f:
                f.write(po_content)
            action = "created"
        
        return {"message": f"PO file {action} for {language}"}
    
    except Exception as e:
        logger.error(f"PO generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/upload-translations/{language}")
async def upload_translations(
    language: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        # Validate language
        lang_code = get_language_code_by_name(db, language)
        if not lang_code:
            error_msg = f"Language '{language}' not found"
            logger.error(error_msg)
            raise HTTPException(status_code=404, detail=error_msg)
        
        # Get file extension
        filename = file.filename.lower()
        if '.' not in filename:
            raise HTTPException(
                status_code=400,
                detail="File has no extension"
            )
        
        ext = filename.rsplit('.', 1)[1]
        
        # Read file content
        content = await file.read()
        
        # Process based on file type
        if ext == 'csv':
            decoded_content = read_csv_file(content)
            csv_file = StringIO(decoded_content)
            reader = csv.reader(csv_file)
            rows = list(reader)
            msgids, translations = extract_translations_from_rows(rows)
            
        elif ext in ['xlsx', 'xls']:
            rows = read_excel_file(content, ext)
            msgids, translations = extract_translations_from_rows(rows)
            
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Use CSV, XLSX, or XLS"
            )
        
        # Validate we have translations
        if not msgids:
            raise HTTPException(
                status_code=400,
                detail="No translations found in file"
            )
        
        # Update database
        process_uploaded_translations(db, lang_code, msgids, translations)
        
        # Generate PO file path
        po_dir = os.path.join(Config.LOCALES_DIR, lang_code, "LC_MESSAGES")
        os.makedirs(po_dir, exist_ok=True)
        po_path = os.path.join(po_dir, "salesplaypos.po")
        
        # Generate PO content
        po_content = generate_po_content(language, lang_code, msgids, translations)
        
        # Write PO file
        with open(po_path, "w", encoding="utf-8") as f:
            f.write(po_content)
        
        return {
            "message": f"Translations uploaded successfully for {language}",
            "translations_processed": len(msgids),
            "po_file_path": po_path
        }
    
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception(f"Translation upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
