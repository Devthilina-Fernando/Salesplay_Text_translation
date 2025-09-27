from fastapi import APIRouter, Depends, HTTPException,File,UploadFile
from fastapi.responses import StreamingResponse, HTMLResponse
from sqlalchemy.orm import Session
from config.database import get_db
from config.logger import logger
from models.language_strings_model import LanguageString
from datetime import datetime
import pandas as pd
from fastapi import UploadFile, File, HTTPException
import io
import numpy as np
from controllers.translation_controller import get_language_code_by_name

router = APIRouter()

@router.post("/excel-import/{language}")
async def import_excel_strings(language: str, db: Session = Depends(get_db), file: UploadFile = File(...)):
    try:
        # Read the Excel file
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # Check required columns exist
        if not all(col in df.columns for col in ['msgid', 'msgstr']):
            raise HTTPException(status_code=400, detail="Excel file must contain 'msgid' and 'msgstr' columns")
        
        # Convert msgstr column to string and handle NaN values
        df['msgstr'] = df['msgstr'].astype(str).replace('nan', '').replace('None', '')
        
        # Filter rows with non-empty msgstr
        valid_rows = df[df['msgstr'].str.strip() != '']
        

        lang_code = get_language_code_by_name(db, language)
        if not lang_code:
            error_msg = f"Language '{language}' not found"
            logger.error(error_msg)
            raise HTTPException(status_code=404, detail=error_msg)
        

        updated_count = 0
        # Update records in database
        for _, row in valid_rows.iterrows():
            result = db.query(LanguageString)\
                .filter(LanguageString.msgid == row['msgid'])\
                .update({lang_code: 1})
            
            if result:
                updated_count += 1
        
        db.commit()
        
        return {
            "message": f"Successfully updated {updated_count} records with {language}",
            "total_valid_rows": len(valid_rows),
            "total_excel_rows": len(df)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")