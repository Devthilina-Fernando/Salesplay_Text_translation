from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import Config
from .logger import logger

Base = declarative_base()

try:

    engine = create_engine(
        Config.SQLALCHEMY_DATABASE_URL,
        echo=True,
        pool_size=10,  
        max_overflow=5,  
        pool_timeout=30, 
        pool_recycle=1800  
    )
    logger.info("SQLAlchemy Engine successfully created with connection pooling.")
except Exception as e:
    logger.error(f"Failed to create SQLAlchemy engine: {e}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Yield database session for FastAPI dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
