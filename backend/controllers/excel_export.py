"""
Excel export controller.

This module handles exporting language strings to Excel format.
"""

import io
from datetime import datetime

import pandas as pd
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from config.logger import logger
from models.language_strings_model import LanguageString


class ExcelExportController:
    """Controller for Excel export operations."""

    def __init__(self, db: Session):
        """
        Initialize Excel export controller.
        
        Args:
            db: SQLAlchemy database session.
        """
        self.db = db

    async def export_language_strings(self) -> StreamingResponse:
        """
        Export language strings to Excel file with empty msgstr values.
        
        Returns:
            StreamingResponse with Excel file.
            
        Raises:
            HTTPException: If export operation fails.
        """
        try:
            logger.info("Starting language strings export")

            # Query msgid and msgstr columns
            results = self.db.query(
                LanguageString.msgid, LanguageString.msgstr
            ).all()

            # Create DataFrame
            df = pd.DataFrame(results, columns=["msgid", "msgstr"])

            # Clear all msgstr values (set to empty string)
            df["msgstr"] = ""

            logger.info(f"Exporting {len(df)} language strings")

            # Create in-memory Excel file
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Translations")

            # Prepare for streaming
            output.seek(0)
            filename = f"language_strings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

            logger.info(f"Export completed: {filename}")

            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

        except Exception as e:
            logger.error(f"Export failed: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# Legacy function wrapper
async def excel_export(db: Session) -> StreamingResponse:
    """
    Export language strings to Excel (legacy wrapper).
    
    Args:
        db: Database session.
        
    Returns:
        StreamingResponse with Excel file.
    """
    controller = ExcelExportController(db)
    return await controller.export_language_strings()