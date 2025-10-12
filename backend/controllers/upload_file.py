"""
File upload controller.

This module handles uploading and processing text files with language strings.
"""

from pathlib import Path
from typing import Dict, List

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from config.logger import logger
from models.language_strings_model import LanguageString


class FileUploadController:
    """Controller for file upload operations."""

    UPLOAD_DIR = Path("uploads")
    ALLOWED_CONTENT_TYPE = "text/plain"
    DEFAULT_FILENAME = "strings.txt"

    def __init__(self, db: Session):
        """
        Initialize file upload controller.
        
        Args:
            db: SQLAlchemy database session.
        """
        self.db = db
        self.UPLOAD_DIR.mkdir(exist_ok=True)

    async def handle_file_upload(self, file: UploadFile) -> Dict[str, str]:
        """
        Handle text file upload.
        
        Args:
            file: Uploaded file.
            
        Returns:
            Dictionary with filename.
            
        Raises:
            HTTPException: If file type is invalid.
        """
        # Validate content type
        if file.content_type != self.ALLOWED_CONTENT_TYPE:
            raise HTTPException(
                status_code=400, detail="Only text files are allowed"
            )

        # Read file contents
        contents = await file.read()

        # Clear existing files
        self._clear_upload_directory()

        # Write new file
        file_path = self.UPLOAD_DIR / file.filename
        file_path.write_bytes(contents)

        logger.info(f"File uploaded: {file.filename}")

        return {"filename": file.filename}

    def insert_new_strings_from_file(
        self, filename: str = DEFAULT_FILENAME
    ) -> Dict[str, any]:
        """
        Insert new strings from uploaded file into database.
        
        Args:
            filename: Name of the file to process.
            
        Returns:
            Dictionary with insertion statistics.
            
        Raises:
            FileNotFoundError: If file doesn't exist.
            Exception: If database operation fails.
        """
        file_path = self.UPLOAD_DIR / filename

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Processing file: {file_path}")

        try:
            # Read non-empty lines
            with open(file_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]

            # Get existing msgids
            existing_msgids = {
                msgid for (msgid,) in self.db.query(LanguageString.msgid).all()
            }

            # Filter duplicates
            to_insert = []
            skipped = []

            for line in lines:
                if line in existing_msgids:
                    skipped.append(line)
                    continue

                to_insert.append(LanguageString(msgid=line, msgstr=line))
                existing_msgids.add(line)  # Prevent duplicates in current file

            # Batch insert
            if to_insert:
                self.db.add_all(to_insert)
                self.db.commit()
                logger.info(f"Inserted {len(to_insert)} new records")

            return {
                "inserted_count": len(to_insert),
                "skipped": skipped,
            }

        except Exception as e:
            logger.error(f"Error inserting strings: {str(e)}", exc_info=True)
            self.db.rollback()
            raise

    def _clear_upload_directory(self) -> None:
        """Clear all files from upload directory."""
        for existing_file in self.UPLOAD_DIR.iterdir():
            if existing_file.is_file():
                existing_file.unlink()


# Legacy function wrappers
async def handle_file_upload(file: UploadFile) -> Dict[str, str]:
    """Handle file upload (legacy wrapper)."""
    controller = FileUploadController(None)  # No DB needed for upload
    return await controller.handle_file_upload(file)


def insert_new_strings_from_file(db: Session) -> Dict[str, any]:
    """Insert new strings from file (legacy wrapper)."""
    controller = FileUploadController(db)
    return controller.insert_new_strings_from_file()