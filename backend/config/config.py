import os
from .logger import logger
from dotenv import load_dotenv
load_dotenv()

class Config:
    """Configuration class to manage environment variables for database connection."""

    MYSQL_HOST = os.getenv("MYSQL_HOST")
    MYSQL_USER = os.getenv("MYSQL_USER")
    MYSQL_PORT = os.getenv("MYSQL_PORT")
    MYSQL_DB = os.getenv("MYSQL_DB")
    # MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")

    SQLALCHEMY_DATABASE_URL = (
        f"mysql+pymysql://{MYSQL_USER}:@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"

        # Uncomment the below line if password is used
        # f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    )

    logger.info(f"Configuring database connection to host: {MYSQL_HOST}, port: {MYSQL_PORT}, database: {MYSQL_DB}")

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    msgfmt_path = os.getenv("MSGFMT_PATH", "msgfmt.exe")

    UPLOAD_DIR = "uploads"
    LOCALES_DIR = "locales"
    
    PORT = os.getenv("PORT")

    

