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

# @router.get("/export")
# async def export_language_strings(db: Session = Depends(get_db)):
#     try:
#         # Query all msgid values
#         results = db.query(LanguageString.msgid).all()
        
#         # Create DataFrame with msgid and empty msgstr column
#         df = pd.DataFrame(results, columns=['msgid'])
#         df['msgstr'] = ""  # Add empty msgstr column
        
#         # Generate filename with timestamp
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         filename = f"language_strings_{timestamp}.xlsx"
        
#         # Save to Excel
#         df.to_excel(filename, index=False, engine='openpyxl')
        
#         # Return file response
#         return FileResponse(
#             filename,
#             media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#             filename=filename
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
#     finally:
#         # Clean up temporary file
#         if os.path.exists(filename):
#             os.remove(filename)

@router.get("/export")
async def export_language_strings(db: Session = Depends(get_db)):
    try:
        # Query only msgid column
        results = db.query(LanguageString.msgid).all()
        msgids = [r[0] for r in results]
        
        # Create DataFrame
        df = pd.DataFrame({
            "msgid": msgids,
            "msgstr": [""] * len(msgids)  # Empty column
        })
        
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