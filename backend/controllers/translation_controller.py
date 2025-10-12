"""
Translation controller for managing translation operations.

This module handles translation generation, PO file creation, file uploads,
and database updates for translation strings.
"""

import asyncio
import csv
import re
from datetime import datetime
from io import BytesIO, StringIO
from pathlib import Path
from typing import List, Optional, Tuple

import zoneinfo
from fastapi import HTTPException, UploadFile
from openai import AsyncOpenAI
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import NoSuchTableError, SQLAlchemyError
from sqlalchemy.orm import Session

from config.config import Config
from config.logger import logger
from models.language_local_model import LanguageLocale
from models.language_strings_model import LanguageString


class TranslationResult(BaseModel):
    """Pydantic model for OpenAI translation response."""

    translated_text: str


class TranslationController:
    """Controller for translation operations."""

    def __init__(self, db: Session):
        """
        Initialize translation controller.
        
        Args:
            db: SQLAlchemy database session.
        """
        self.db = db
        self.client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)
        self.max_concurrency = 20
        self.batch_size = 500

    # ==================== Translation Operations ====================

    def get_zero_msgids(self, lang_column: str) -> List[str]:
        """
        Get all message IDs that haven't been translated for a language.
        
        Args:
            lang_column: Language code column name.
            
        Returns:
            List of untranslated message IDs.
            
        Raises:
            ValueError: If language column doesn't exist.
            RuntimeError: If table doesn't exist.
        """
        try:
            logger.info(f"Getting zero msgids for: {lang_column}")

            if not hasattr(LanguageString, lang_column):
                error_msg = f"Invalid language column: {lang_column}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            column_attr = getattr(LanguageString, lang_column)
            query = (
                self.db.query(LanguageString.msgid)
                .filter(column_attr == 0)
                .order_by(LanguageString.id)
            )

            return [row.msgid for row in query.all()]

        except NoSuchTableError:
            error_msg = f"Table '{LanguageString.__tablename__}' does not exist"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        except Exception as e:
            logger.error(f"Error getting zero msgids: {str(e)}", exc_info=True)
            raise

    async def translate_msgids(
        self, msgids: List[str], lang_name: str, lang_code: str
    ) -> List[str]:
        """
        Translate message IDs to target language using OpenAI.
        
        Args:
            msgids: List of message IDs to translate.
            lang_name: Target language name.
            lang_code: Target language code.
            
        Returns:
            List of translated strings.
        """
        logger.info(f"Translating {len(msgids)} strings to {lang_name}")
        translations = []

        # Process in batches
        for i in range(0, len(msgids), self.batch_size):
            batch = msgids[i : i + self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = (len(msgids) - 1) // self.batch_size + 1

            logger.info(f"Processing batch {batch_num}/{total_batches}")

            batch_translations = await self._process_translation_batch(
                batch, lang_name, lang_code
            )
            translations.extend(batch_translations)

        return translations

    async def _process_translation_batch(
        self, batch_msgids: List[str], lang_name: str, lang_code: str
    ) -> List[str]:
        """
        Process a batch of translations with concurrent API calls.
        
        Args:
            batch_msgids: Batch of message IDs.
            lang_name: Target language name.
            lang_code: Target language code.
            
        Returns:
            List of translated strings for the batch.
        """
        semaphore = asyncio.Semaphore(self.max_concurrency)
        tasks = [
            self._translate_single_text(msgid, lang_name, semaphore)
            for msgid in batch_msgids
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        batch_translations = []
        success_msgids = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"Error translating '{batch_msgids[i]}': {str(result)}",
                    exc_info=True,
                )
                batch_translations.append(batch_msgids[i])  # Fallback to original
            else:
                batch_translations.append(result)
                success_msgids.append(batch_msgids[i])

        # Update database for successful translations
        if success_msgids:
            self._bulk_update_translation_status(success_msgids, lang_code)

        return batch_translations

    async def _translate_single_text(
        self, text: str, lang_name: str, semaphore: asyncio.Semaphore
    ) -> str:
        """
        Translate a single text string using OpenAI API.
        
        Args:
            text: Text to translate.
            lang_name: Target language name.
            semaphore: Semaphore for rate limiting.
            
        Returns:
            Translated text.
        """
        system_prompt = (
            "You are a professional POS translator. Translate text while EXACTLY preserving: "
            "• Punctuation, numbers, symbols, and formatting\n"
            "NEVER add/remove quotes or other characters.\n"
            "Return ONLY the translated text.\n"
            "STRICTLY DO NOT ADD ANY UNWANTED PUNCTUATION MARKS APART FROM THE GIVEN"
        )

        async with semaphore:
            response = await self.client.responses.parse(
                model="gpt-4o-2024-08-06",
                input=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Translate the following to {lang_name} exactly as requested:\n\n{text}",
                    },
                ],
                text_format=TranslationResult,
            )
            return response.output_parsed.translated_text

    def _bulk_update_translation_status(
        self, msgids: List[str], lang_code: str
    ) -> None:
        """
        Bulk update translation status in database.
        
        Args:
            msgids: List of message IDs that were translated.
            lang_code: Language code column to update.
        """
        try:
            records = (
                self.db.query(LanguageString)
                .filter(LanguageString.msgid.in_(msgids))
                .all()
            )

            record_dict = {r.msgid: r for r in records}
            not_found = []

            for msgid in msgids:
                if msgid in record_dict:
                    setattr(record_dict[msgid], lang_code, 1)
                else:
                    not_found.append(msgid)

            self.db.commit()

            if not_found:
                logger.warning(f"No records found for {len(not_found)} msgids")

        except Exception as e:
            self.db.rollback()
            logger.error(f"Database commit failed: {str(e)}", exc_info=True)
            raise

    # ==================== PO File Operations ====================

    def generate_po_content(
        self, lang_name: str, lang_code: str, msgids: List[str], translations: List[str]
    ) -> str:
        """
        Generate PO file content from translations.
        
        Args:
            lang_name: Language name.
            lang_code: Language code.
            msgids: List of message IDs.
            translations: List of translated strings.
            
        Returns:
            Complete PO file content as string.
        """
        logger.info("Generating PO content")

        tz = zoneinfo.ZoneInfo("Asia/Colombo")
        now = datetime.now(tz)
        timestamp = now.strftime("%Y-%m-%d %H:%M%z")

        header = [
            "# Autogenerated by SalesPlay Translate development",
            "#",
            f"# language: {lang_name}",
            f"# locale: {lang_code}",
            f'# date: {datetime.now().strftime("%Y-%m-%d")}',
            "#",
            'msgid ""',
            'msgstr ""',
            '"Project-Id-Version: SalesPlay POS Translation-0.000\\n"',
            f'"POT-Creation-Date: {timestamp}\\n"',
            f'"PO-Revision-Date: {timestamp}\\n"',
            '"Last-Translator: SalesPlay Team\\n"',
            '"Language-Team: SalesPlay (Pvt) Ltd <support@nvision.lk>\\n"',
            '"Language: en\\n"',
            '"MIME-Version: 1.0\\n"',
            '"Content-Type: text/plain; charset=UTF-8\\n"',
            '"Content-Transfer-Encoding: 8bit\\n"',
            '"Plural-Forms: nplurals=2; plural=n != 1;\\n"',
            '"X-Generator: Poedit 3.0.1\\n"',
            "",
        ]

        entries = []
        for msgid, msgstr in zip(msgids, translations):
            escaped_msgid = msgid.replace('"', '\\"').replace("\n", "\\n")
            escaped_msgstr = msgstr.replace('"', '\\"').replace("\n", "\\n")
            entries.append(f'msgid "{escaped_msgid}"')
            entries.append(f'msgstr "{escaped_msgstr}"\n')

        return "\n".join(header + entries)

    def update_po_content(
        self,
        existing_content: str,
        lang_name: str,
        new_msgids: List[str],
        new_translations: List[str],
    ) -> str:
        """
        Update existing PO file with new translations.
        
        Args:
            existing_content: Current PO file content.
            lang_name: Language name.
            new_msgids: New message IDs to add.
            new_translations: New translations to add.
            
        Returns:
            Updated PO file content.
        """
        # Update revision date
        tz = zoneinfo.ZoneInfo("Asia/Colombo")
        now = datetime.now(tz)
        timestamp = now.strftime("%Y-%m-%d %H:%M%z")

        existing_content = re.sub(
            r'(# date: )[\d-]+', f'\\g<1>{datetime.now().strftime("%Y-%m-%d")}', existing_content
        )
        existing_content = re.sub(
            r'("PO-Revision-Date: )[\d:\s+-]+(?=\\n")',
            f"\\g<1>{timestamp}",
            existing_content,
        )

        # Extract header and body
        header_end = existing_content.find('msgstr ""') + len('msgstr ""') + 1
        header = existing_content[:header_end]
        body = existing_content[header_end:]

        # Parse existing translations
        existing_translations = {}
        for match in re.finditer(r'msgid "(.*?)"\nmsgstr "(.*?)"\n', body, re.DOTALL):
            msgid = match.group(1).replace('\\"', '"').replace("\\n", "\n")
            msgstr = match.group(2).replace('\\"', '"').replace("\\n", "\n")
            existing_translations[msgid] = msgstr

        # Ensure proper spacing
        if body and not body.endswith("\n\n"):
            body = body.rstrip() + "\n\n"

        # Add new translations
        for msgid, translation in zip(new_msgids, new_translations):
            if msgid not in existing_translations:
                escaped_id = msgid.replace('"', '\\"').replace("\n", "\\n")
                escaped_tr = translation.replace('"', '\\"').replace("\n", "\\n")
                body += f'msgid "{escaped_id}"\n'
                body += f'msgstr "{escaped_tr}"\n\n'

        return header + body

    # ==================== File Upload Operations ====================

    def read_csv_file(self, content: bytes) -> str:
        """
        Read CSV file with encoding detection.
        
        Args:
            content: CSV file bytes.
            
        Returns:
            Decoded CSV content as string.
            
        Raises:
            HTTPException: If file cannot be decoded.
        """
        encodings = ["utf-8", "latin-1", "cp1252", "utf-16"]

        for encoding in encodings:
            try:
                decoded_content = content.decode(encoding)
                logger.info(f"Successfully decoded CSV using {encoding} encoding")
                return decoded_content
            except UnicodeDecodeError:
                continue

        raise HTTPException(
            status_code=400,
            detail="Unable to decode file. Supported encodings: UTF-8, Latin-1, CP1252, UTF-16",
        )

    def read_excel_file(self, content: bytes, file_extension: str) -> List[tuple]:
        """
        Read Excel file (XLSX or XLS).
        
        Args:
            content: Excel file bytes.
            file_extension: File extension ('xlsx' or 'xls').
            
        Returns:
            List of row tuples.
            
        Raises:
            HTTPException: If file cannot be read.
        """
        try:
            if file_extension == "xlsx":
                from openpyxl import load_workbook

                wb = load_workbook(filename=BytesIO(content))
                sheet = wb.active
                rows = sheet.iter_rows(values_only=True)
                return list(rows)

            elif file_extension == "xls":
                import xlrd

                book = xlrd.open_workbook(file_contents=content)
                sheet = book.sheet_by_index(0)
                return [sheet.row_values(row) for row in range(sheet.nrows)]

        except ImportError:
            logger.error("Excel library not installed")
            raise HTTPException(
                status_code=500,
                detail="Excel processing requires openpyxl for XLSX or xlrd for XLS files",
            )

        except Exception as e:
            logger.error(f"Excel read error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=400, detail=f"Invalid Excel file: {str(e)}"
            )

    def extract_translations_from_rows(
        self, rows: List[tuple]
    ) -> Tuple[List[str], List[str]]:
        """
        Extract msgid and msgstr from CSV/Excel rows.
        
        Args:
            rows: List of row tuples from file.
            
        Returns:
            Tuple of (msgids, translations) lists.
            
        Raises:
            HTTPException: If file format is invalid.
        """
        if len(rows) < 1:
            raise HTTPException(status_code=400, detail="File is empty")

        # Parse headers
        headers = [str(cell).lower() if cell else "" for cell in rows[0]]

        try:
            msgid_index = headers.index("msgid")
            msgstr_index = headers.index("msgstr")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="File must contain 'msgid' and 'msgstr' columns",
            )

        # Extract data
        msgids = []
        translations = []

        for line_number, row in enumerate(rows[1:], start=2):
            try:
                row_data = list(row) if isinstance(row, tuple) else row

                if len(row_data) <= max(msgid_index, msgstr_index):
                    raise ValueError(f"Missing values in row {line_number}")

                msgid = str(row_data[msgid_index]) if row_data[msgid_index] is not None else ""
                msgstr = (
                    str(row_data[msgstr_index]) if row_data[msgstr_index] is not None else ""
                )

                msgids.append(msgid)
                translations.append(msgstr)

            except Exception as e:
                logger.error(f"Error processing row {line_number}: {str(e)}")
                raise HTTPException(
                    status_code=400, detail=f"Error in row {line_number}: {str(e)}"
                )

        return msgids, translations

    def process_uploaded_translations(
        self, lang_code: str, msgids: List[str], translations: List[str]
    ) -> None:
        """
        Update database with uploaded translations.
        
        Args:
            lang_code: Language code column to update.
            msgids: List of message IDs.
            translations: List of translations.
            
        Raises:
            ValueError: If list lengths don't match.
        """
        if len(msgids) != len(translations):
            raise ValueError("msgids and translations lists must have the same length")

        records = (
            self.db.query(LanguageString)
            .filter(LanguageString.msgid.in_(msgids))
            .all()
        )

        record_dict = {r.msgid: r for r in records}
        not_found = []

        for i, msgid in enumerate(msgids):
            if msgid in record_dict:
                setattr(record_dict[msgid], f"translation_{lang_code}", translations[i])
            else:
                new_record = LanguageString(
                    msgid=msgid, **{f"translation_{lang_code}": translations[i]}
                )
                self.db.add(new_record)
                not_found.append(msgid)

        try:
            self.db.commit()
            if not_found:
                logger.info(f"Created {len(not_found)} new records")

        except Exception as e:
            self.db.rollback()
            logger.error(f"Database commit failed: {str(e)}", exc_info=True)
            raise

    # ==================== Utility Functions ====================

    def get_language_code_by_name(self, language: str) -> Optional[str]:
        """
        Get language code by language name.
        
        Args:
            language: Language name.
            
        Returns:
            Language code or None if not found.
            
        Raises:
            SQLAlchemyError: If database query fails.
        """
        try:
            logger.info(f"Getting language code for: {language}")
            record = (
                self.db.query(LanguageLocale.language_code)
                .filter(LanguageLocale.language == language)
                .first()
            )
            return record[0] if record else None

        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}", exc_info=True)
            raise


# Legacy function wrappers for backward compatibility
def get_zero_msgids(db: Session, lang_column: str) -> List[str]:
    """Get zero msgids (legacy wrapper)."""
    controller = TranslationController(db)
    return controller.get_zero_msgids(lang_column)


async def translate_msgids(
    db: Session, msgids: List[str], lang_name: str, lang_code: str
) -> List[str]:
    """Translate msgids (legacy wrapper)."""
    controller = TranslationController(db)
    return await controller.translate_msgids(msgids, lang_name, lang_code)


def generate_po_content(
    lang_name: str, lang_code: str, msgids: List[str], translations: List[str]
) -> str:
    """Generate PO content (legacy wrapper)."""
    controller = TranslationController(None)  # No DB needed for this operation
    return controller.generate_po_content(lang_name, lang_code, msgids, translations)


def update_po_content(
    existing_content: str,
    lang_name: str,
    new_msgids: List[str],
    new_translations: List[str],
) -> str:
    """Update PO content (legacy wrapper)."""
    controller = TranslationController(None)
    return controller.update_po_content(
        existing_content, lang_name, new_msgids, new_translations
    )


def get_language_code_by_name(db: Session, language: str) -> Optional[str]:
    """Get language code by name (legacy wrapper)."""
    controller = TranslationController(db)
    return controller.get_language_code_by_name(language)


def read_csv_file(content: bytes) -> str:
    """Read CSV file (legacy wrapper)."""
    controller = TranslationController(None)
    return controller.read_csv_file(content)


def read_excel_file(content: bytes, ext: str) -> List[tuple]:
    """Read Excel file (legacy wrapper)."""
    controller = TranslationController(None)
    return controller.read_excel_file(content, ext)


def extract_translations_from_rows(rows: List[tuple]) -> Tuple[List[str], List[str]]:
    """Extract translations from rows (legacy wrapper)."""
    controller = TranslationController(None)
    return controller.extract_translations_from_rows(rows)


def process_uploaded_translations(
    db: Session, lang_code: str, msgids: List[str], translations: List[str]
) -> None:
    """Process uploaded translations (legacy wrapper)."""
    controller = TranslationController(db)
    return controller.process_uploaded_translations(lang_code, msgids, translations)