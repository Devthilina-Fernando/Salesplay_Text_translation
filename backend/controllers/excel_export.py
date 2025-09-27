from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from config.logger import logger
from models.language_strings_model import LanguageString
from datetime import datetime
import pandas as pd
import io

async def excel_export(db: Session) -> StreamingResponse:
    """
    Export language strings as Excel file with empty msgstr values
    
    Args:
        db: Database session
        
    Returns:
        StreamingResponse: Excel file as streaming response
    """
    try:
        # Query both msgid and msgstr columns
        results = db.query(LanguageString.msgid, LanguageString.msgstr).all()
        
        # Create DataFrame from the results
        df = pd.DataFrame(results, columns=["msgid", "msgstr"])
        
        # Clear all msgstr values (set to empty string)
        df['msgstr'] = ''
        
        # Create in-memory Excel file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Translations')
        
        # Prepare for streaming
        output.seek(0)
        filename = f"language_strings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))