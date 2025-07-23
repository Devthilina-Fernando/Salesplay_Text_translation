from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from pathlib import Path
import os
from controllers.po_compiler import POCompilerController
from config.logger import logger
from sqlalchemy.orm import Session
from config.database import get_db
from controllers.translation_controller import get_language_code_by_name

# # Configuration
# BASE_DIR = Path(__file__).resolve().parent.parent
# LOCALES_DIR = BASE_DIR / "locales"
# PO_DIR = LOCALES_DIR / "si_SI/LC_MESSAGES"
# PO_FILE = "salesplaypos.po"
# MO_FILE = "salesplaypos.mo"

# # Allow custom msgfmt path via environment variable
# MSG_FMT_PATH = os.environ.get("MSG_FMT_PATH")

router = APIRouter()

@router.post("/compile-po/{language}")
async def compile_po_endpoint(language: str,
    db: Session = Depends(get_db)):
    try:
        lang_code = get_language_code_by_name(db, language)
        if not lang_code:
            error_msg = f"Language '{language}' not found"
            logger.error(error_msg)
            raise HTTPException(status_code=404, detail=error_msg)   

        BASE_DIR = Path(__file__).resolve().parent.parent
        LOCALES_DIR = BASE_DIR / "locales"        
        PO_DIR = LOCALES_DIR / f"{lang_code}/LC_MESSAGES"
        PO_FILE = "salesplaypos.po"
        MO_FILE = "salesplaypos.mo"

        controller = POCompilerController(PO_DIR, PO_FILE, MO_FILE)

    except Exception as e:
        logger.error(f"PO generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 
    return controller.compile_po()