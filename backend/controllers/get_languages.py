from typing import List
from config.logger import logger

from sqlalchemy.orm import Session
from sqlalchemy import distinct
from sqlalchemy.exc import SQLAlchemyError

from models.language_local_model import LanguageLocale  


def get_all_languages(db_session: Session) -> List[str]:
    # Retrieve all distinct language codes from the LanguageLocale table.
    try:
    
        rows = db_session.query(distinct(LanguageLocale.language)).all()
        return [language for (language,) in rows]
    
    except SQLAlchemyError as exc:
        
        # Roll back any pending transaction and log the error
        db_session.rollback()
        logger.exception("Failed to fetch distinct languages")

        raise RuntimeError("Could not retrieve languages from the database") from exc
