from sqlalchemy import DDL, inspect, text, insert, delete,Column, Integer
from schemas.translation import LanguageLocaleCreate
from sqlalchemy.orm import Session
from config.logger import logger
from models.language_local_model import LanguageLocale
from datetime import datetime
from models.language_strings_model import LanguageString
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from datetime import datetime

def add_language_locale(db: Session, locale_data: LanguageLocaleCreate):
    logger.info(f"Adding new language: {locale_data.language_name}")
    
    # Check if locale already exists
    existing = db.query(LanguageLocale).filter(
        LanguageLocale.language_code == locale_data.language_code
    ).first()
    
    if existing:
        error_msg = f"Language code {locale_data.language_code} already exists"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Generate and insert with new ID (with retries for concurrency)
    retries = 5
    locale_id = None
    
    while retries > 0:
        try:
            # Get all existing IDs to find smallest available
            result = db.execute(text("SELECT id FROM language_locales")).fetchall()
            existing_ids = {row[0] for row in result} if result else set()
            
            candidate = 0
            while candidate in existing_ids:
                candidate += 1

            stmt = insert(LanguageLocale.__table__).values(
                id=candidate,
                language=locale_data.language,
                language_code=locale_data.language_code,
                language_name=locale_data.language_name,
                is_enable=locale_data.is_enable,
                last_update=datetime.utcnow()
            )
            db.execute(stmt)
            db.commit()
            locale_id = candidate
            logger.info(f"Created language locale: ID {locale_id}")
            break 

        except IntegrityError as e:
            db.rollback()
            if "Duplicate entry" in str(e.orig) and "for key 'PRIMARY'" in str(e.orig):
                retries -= 1
                if retries == 0:
                    logger.error("Failed after 5 retries due to duplicate primary keys")
                    
                    return None
                logger.warning(f"Duplicate primary key, retrying... ({retries} left)")
            else:
                logger.error(f"Database error creating locale: {str(e)}")
                
                return None

        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error creating locale: {str(e)}")
            
            return None

    if locale_id is None:
        logger.error("Failed to create language locale after all retries")
        return None

    # Add new column to language_strings table
    try:
        table_name = LanguageString.__tablename__
        column_name = locale_data.language_code
        
        # Check if column already exists
        inspector = inspect(db.bind)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        if column_name in columns:
            error_msg = f"Column {column_name} already exists in {table_name}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Find position before last_update column
        if 'last_update' not in columns:
            error_msg = f"Critical: 'last_update' column missing in {table_name}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
            
        last_update_idx = columns.index('last_update')
        after_column = columns[last_update_idx - 1] if last_update_idx > 0 else None
        
        # Get quoted identifiers
        dialect = db.bind.dialect
        preparer = dialect.identifier_preparer
        table_name_quoted = preparer.quote(table_name)
        column_name_quoted = preparer.quote(column_name)
        escaped_comment = locale_data.language_name.replace("'", "''")
        
        # Build ALTER TABLE statement with position
        if after_column:
            after_column_quoted = preparer.quote(after_column)
            sql = text(
                f"ALTER TABLE {table_name_quoted} "
                f"ADD COLUMN {column_name_quoted} INTEGER DEFAULT 0 "
                f"COMMENT '{escaped_comment}' "
                f"AFTER {after_column_quoted}"
            )
        else:
            # If last_update is first column (unlikely but safe)
            sql = text(
                f"ALTER TABLE {table_name_quoted} "
                f"ADD COLUMN {column_name_quoted} INTEGER DEFAULT 0 "
                f"COMMENT '{escaped_comment}' FIRST"
            )
        
        # Execute DDL statement
        with db.bind.connect() as connection:
            connection.execute(sql)
            connection.commit()
        
        logger.info(f"Added column {column_name} to {table_name} before last_update")

    except Exception as e:
        # Rollback locale creation if column creation fails
        try:
            delete_stmt = delete(LanguageLocale.__table__).where(
                LanguageLocale.id == locale_id
            )
            db.execute(delete_stmt)
            db.commit()
            logger.warning(f"Rolled back locale creation for ID {locale_id}")
        except Exception as rollback_error:
            logger.critical(f"Failed to rollback locale creation: {str(rollback_error)}")
            raise RuntimeError(f"Critical error during rollback: {str(rollback_error)}")
        
        logger.error(f"Column creation failed: {str(e)}")
        raise RuntimeError(f"Column creation failed: {str(e)}")
    
    return {
        "id": locale_id,
        "language_code": locale_data.language_code
    }