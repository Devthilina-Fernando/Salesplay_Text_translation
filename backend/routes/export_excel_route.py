from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from sqlalchemy.orm import Session
from config.database import get_db
from config.logger import logger
from models.language_strings_model import LanguageString
from datetime import datetime
import pandas as pd
import os
import io

router = APIRouter()

@router.get("/export")
async def export_language_strings(db: Session = Depends(get_db)):
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