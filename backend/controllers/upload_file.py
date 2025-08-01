from fastapi import HTTPException, UploadFile
from pathlib import Path
from config.logger import logger
from sqlalchemy.orm import Session
from models.language_strings_model import LanguageString
import os
from typing import Dict, List

async def handle_file_upload(file: UploadFile):

    if file.content_type != "text/plain":
        raise HTTPException(status_code=400, detail="Only text files are allowed")

    # Read all contents 
    contents = await file.read()

    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)

    # Clear out any existing files
    for existing in upload_dir.iterdir():
        existing.unlink()

    # Write the new file
    file_path = upload_dir / file.filename
    file_path.write_bytes(contents)

    return {"filename": file.filename}


def insert_new_strings_from_file(db: Session) -> Dict[str, int | List[dict]]:
    try:
        filename = 'strings.txt'
        file_path = os.path.join('uploads', filename)
        logger.info(f"Processing file: {file_path}")
        
        # Read all non-empty lines from file
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        # Fetch existing msgids from database
        existing_msgids = {msgid for (msgid,) in db.query(LanguageString.msgid).all()}
        
        to_insert = []
        skipped = []
        
        for line in lines:
            # Skip duplicates (existing in DB or current batch)
            if line in existing_msgids:
                # skipped.append({"msgid": line, "reason": "duplicate"})
                skipped.append(line)
                continue
            
            # Add to insertion list and track in existing_msgids
            to_insert.append(LanguageString(msgid=line, msgstr=line))
            existing_msgids.add(line)  # Prevent duplicates in current file
        
        # Batch insert new records
        if to_insert:
            db.add_all(to_insert)
            db.commit()
            logger.info(f"Inserted {len(to_insert)} new records")
        
        return {
            "inserted_count": len(to_insert),
            "skipped": skipped
        }
    
    except Exception as e:
        logger.error(f"Error inserting strings: {str(e)}")
        db.rollback()
        raise