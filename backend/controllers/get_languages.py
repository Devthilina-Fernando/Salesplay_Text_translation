"""
Language retrieval controller.

This module handles fetching language information from the database.
"""

from typing import List

from sqlalchemy import distinct
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from config.logger import logger
from models.language_local_model import LanguageLocale


class LanguageController:
    """Controller for language retrieval operations."""

    def __init__(self, db: Session):
        """
        Initialize language controller.
        
        Args:
            db: SQLAlchemy database session.
        """
        self.db = db

    def get_all_languages(self) -> List[str]:
        """
        Retrieve all distinct language names from the database.
        
        Returns:
            List of unique language names.
            
        Raises:
            RuntimeError: If database query fails.
        """
        try:
            rows = self.db.query(distinct(LanguageLocale.language)).all()
            languages = [language for (language,) in rows]
            
            logger.info(
                "Retrieved languages",
                extra={"count": len(languages)},
            )
            
            return languages

        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.exception("Failed to fetch distinct languages")
            raise RuntimeError("Could not retrieve languages from the database") from exc


# Legacy function wrapper
def get_all_languages(db_session: Session) -> List[str]:
    """
    Retrieve all distinct language codes (legacy wrapper).
    
    Args:
        db_session: Database session.
        
    Returns:
        List of language names.
    """
    controller = LanguageController(db_session)
    return controller.get_all_languages()