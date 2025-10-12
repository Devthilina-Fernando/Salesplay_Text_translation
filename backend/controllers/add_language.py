"""
Language locale management controller.

This module handles adding new language locales to the system, including
creating database records and adding corresponding columns to the translation table.
"""

from datetime import datetime
from typing import Dict, Optional, Set

from sqlalchemy import inspect, text, insert, delete
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from config.logger import logger
from models.language_local_model import LanguageLocale
from models.language_strings_model import LanguageString
from schemas.translation import LanguageLocaleCreate


class LanguageLocaleController:
    """Controller for language locale operations."""

    MAX_RETRIES = 5

    def __init__(self, db: Session):
        """
        Initialize controller with database session.
        
        Args:
            db: SQLAlchemy database session.
        """
        self.db = db

    def add_language_locale(self, locale_data: LanguageLocaleCreate) -> Dict[str, any]:
        """
        Add a new language locale and create corresponding translation column.
        
        This operation is transactional - if column creation fails, the locale
        record is rolled back.
        
        Args:
            locale_data: Language locale creation schema.
            
        Returns:
            Dictionary containing the new locale ID and language code.
            
        Raises:
            ValueError: If language code already exists or validation fails.
            RuntimeError: If database operations fail.
        """
        logger.info(
            "Adding new language",
            extra={
                "language_name": locale_data.language_name,
                "language_code": locale_data.language_code,
            },
        )

        # Check for existing locale
        self._validate_unique_language(locale_data.language_code)

        # Create locale with retry logic for concurrency
        locale_id = self._create_locale_with_retry(locale_data)
        if locale_id is None:
            raise RuntimeError("Failed to create language locale after all retries")

        # Add translation column
        try:
            self._add_translation_column(locale_data)
            logger.info(
                "Language locale created successfully",
                extra={
                    "locale_id": locale_id,
                    "language_code": locale_data.language_code,
                },
            )
            return {"id": locale_id, "language_code": locale_data.language_code}

        except Exception as e:
            # Rollback locale creation if column creation fails
            self._rollback_locale_creation(locale_id)
            logger.error(f"Column creation failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"Column creation failed: {str(e)}") from e

    def _validate_unique_language(self, language_code: str) -> None:
        """
        Check if language code already exists.
        
        Args:
            language_code: Language code to validate.
            
        Raises:
            ValueError: If language code already exists.
        """
        existing = (
            self.db.query(LanguageLocale)
            .filter(LanguageLocale.language_code == language_code)
            .first()
        )

        if existing:
            error_msg = f"Language code {language_code} already exists"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def _create_locale_with_retry(
        self, locale_data: LanguageLocaleCreate
    ) -> Optional[int]:
        """
        Create locale record with retry logic for handling concurrent inserts.
        
        Args:
            locale_data: Language locale data.
            
        Returns:
            Created locale ID or None if all retries failed.
        """
        retries = self.MAX_RETRIES

        while retries > 0:
            try:
                locale_id = self._generate_next_available_id()
                stmt = insert(LanguageLocale.__table__).values(
                    id=locale_id,
                    language=locale_data.language,
                    language_code=locale_data.language_code,
                    language_name=locale_data.language_name,
                    is_enable=locale_data.is_enable,
                    last_update=datetime.utcnow(),
                )
                self.db.execute(stmt)
                self.db.commit()

                logger.info(f"Created language locale with ID: {locale_id}")
                return locale_id

            except IntegrityError as e:
                self.db.rollback()
                if self._is_duplicate_key_error(e):
                    retries -= 1
                    if retries == 0:
                        logger.error("Failed after all retries due to duplicate keys")
                        return None
                    logger.warning(f"Duplicate key detected, retrying ({retries} left)")
                else:
                    logger.error(f"Database error creating locale: {str(e)}")
                    return None

            except Exception as e:
                self.db.rollback()
                logger.error(f"Unexpected error creating locale: {str(e)}", exc_info=True)
                return None

        return None

    def _generate_next_available_id(self) -> int:
        """
        Find the smallest available ID in the sequence.
        
        Returns:
            Next available ID (starting from 0).
        """
        result = self.db.execute(text("SELECT id FROM language_locales")).fetchall()
        existing_ids: Set[int] = {row[0] for row in result} if result else set()

        candidate = 0
        while candidate in existing_ids:
            candidate += 1

        return candidate

    def _add_translation_column(self, locale_data: LanguageLocaleCreate) -> None:
        """
        Add new column to language_strings table for the new language.
        
        Args:
            locale_data: Language locale data.
            
        Raises:
            ValueError: If column already exists or validation fails.
            RuntimeError: If DDL execution fails.
        """
        table_name = LanguageString.__tablename__
        column_name = locale_data.language_code

        # Validate column doesn't exist
        inspector = inspect(self.db.bind)
        columns = [col["name"] for col in inspector.get_columns(table_name)]

        if column_name in columns:
            error_msg = f"Column {column_name} already exists in {table_name}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Find position before last_update column
        if "last_update" not in columns:
            error_msg = f"Critical: 'last_update' column missing in {table_name}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        last_update_idx = columns.index("last_update")
        after_column = columns[last_update_idx - 1] if last_update_idx > 0 else None

        # Build and execute ALTER TABLE statement
        sql = self._build_alter_table_sql(
            table_name, column_name, locale_data.language_name, after_column
        )

        with self.db.bind.connect() as connection:
            connection.execute(sql)
            connection.commit()

        logger.info(f"Added column {column_name} to {table_name}")

    def _build_alter_table_sql(
        self,
        table_name: str,
        column_name: str,
        language_name: str,
        after_column: Optional[str] = None,
    ) -> text:
        """
        Build ALTER TABLE SQL statement with proper quoting.
        
        Args:
            table_name: Name of the table.
            column_name: Name of the new column.
            language_name: Language name for comment.
            after_column: Column to insert after (None for FIRST).
            
        Returns:
            SQLAlchemy text object with parameterized SQL.
        """
        dialect = self.db.bind.dialect
        preparer = dialect.identifier_preparer

        table_name_quoted = preparer.quote(table_name)
        column_name_quoted = preparer.quote(column_name)
        escaped_comment = language_name.replace("'", "''")

        if after_column:
            after_column_quoted = preparer.quote(after_column)
            sql = text(
                f"ALTER TABLE {table_name_quoted} "
                f"ADD COLUMN {column_name_quoted} INTEGER DEFAULT 0 "
                f"COMMENT '{escaped_comment}' "
                f"AFTER {after_column_quoted}"
            )
        else:
            sql = text(
                f"ALTER TABLE {table_name_quoted} "
                f"ADD COLUMN {column_name_quoted} INTEGER DEFAULT 0 "
                f"COMMENT '{escaped_comment}' FIRST"
            )

        return sql

    def _rollback_locale_creation(self, locale_id: int) -> None:
        """
        Rollback locale creation if column addition fails.
        
        Args:
            locale_id: ID of the locale to remove.
        """
        try:
            delete_stmt = delete(LanguageLocale.__table__).where(
                LanguageLocale.id == locale_id
            )
            self.db.execute(delete_stmt)
            self.db.commit()
            logger.warning(f"Rolled back locale creation for ID {locale_id}")

        except Exception as rollback_error:
            logger.critical(
                f"Failed to rollback locale creation: {str(rollback_error)}",
                exc_info=True,
            )
            raise RuntimeError(
                f"Critical error during rollback: {str(rollback_error)}"
            ) from rollback_error

    @staticmethod
    def _is_duplicate_key_error(error: IntegrityError) -> bool:
        """
        Check if error is a duplicate primary key error.
        
        Args:
            error: IntegrityError exception.
            
        Returns:
            True if duplicate key error, False otherwise.
        """
        error_msg = str(error.orig).lower()
        return "duplicate entry" in error_msg and "primary" in error_msg


# Factory function for backward compatibility
def add_language_locale(db: Session, locale_data: LanguageLocaleCreate) -> Dict[str, any]:
    """
    Add a new language locale (legacy function wrapper).
    
    Args:
        db: Database session.
        locale_data: Language locale creation data.
        
    Returns:
        Dictionary with locale ID and language code.
    """
    controller = LanguageLocaleController(db)
    return controller.add_language_locale(locale_data)