from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from config.database import get_db
from config.logger import logger
from controllers.translation_controller import (
    get_zero_msgids,
    translate_msgids,
    generate_po_content,
    get_language_code_by_name,
    update_po_content
)
import os
from config.config import Config

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


