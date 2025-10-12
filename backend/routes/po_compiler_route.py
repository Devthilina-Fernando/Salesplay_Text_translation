"""
PO compiler API routes.

This module defines endpoints for compiling PO files to MO files.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from config.database import get_db
from config.logger import logger
from controllers.po_compiler import POCompilerController
from controllers.translation_controller import get_language_code_by_name

router = APIRouter(tags=["localization"])


@router.post(
    "/compile-po/{language}",
    status_code=status.HTTP_200_OK,
    summary="Compile PO to MO",
    description="Compile .po file to .mo file for specified language",
)
async def compile_po_endpoint(
    language: str, db: Session = Depends(get_db)
) -> dict:
    """
    Compile PO file to MO file using msgfmt.
    
    The .po file must exist in the locales directory for the specified language.
    
    Args:
        language: Language name (e.g., "Spanish", "French").
        db: Database session (injected).
        
    Returns:
        Dictionary with compilation status and details.
        
    Raises:
        HTTPException: If language not found or compilation fails.
    """
    try:
        # Validate language exists
        lang_code = get_language_code_by_name(db, language)
        if not lang_code:
            error_msg = f"Language '{language}' not found"
            logger.error(error_msg)
            raise HTTPException(status_code=404, detail=error_msg)

        # Set up paths
        BASE_DIR = Path(__file__).resolve().parent.parent
        LOCALES_DIR = BASE_DIR / "locales"
        PO_DIR = LOCALES_DIR / f"{lang_code}/LC_MESSAGES"
        PO_FILE = "salesplaypos.po"
        MO_FILE = "salesplaypos.mo"

        # Create compiler and compile
        controller = POCompilerController(PO_DIR, PO_FILE, MO_FILE)
        result = controller.compile_po()

        logger.info(
            "PO compilation successful",
            extra={"language": language, "lang_code": lang_code},
        )

        return result

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"PO compilation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))