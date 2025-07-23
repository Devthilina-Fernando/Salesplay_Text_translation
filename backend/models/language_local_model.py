from sqlalchemy import Column, BigInteger, String, Integer, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class LanguageLocale(Base):
    __tablename__ = 'language_locales'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    language = Column(String(192), nullable=False)
    language_code = Column(String(48), nullable=False)
    language_name = Column(String(384), nullable=False)
    is_enable = Column(Integer, nullable=False, default=1)
    last_update = Column(TIMESTAMP)

    # def __repr__(self):
    #     return (
    #         f"<LanguageLocale(id={self.id}, language={self.language!r}, "
    #         f"language_code={self.language_code!r}, language_name={self.language_name!r}, "
    #         f"is_enable={self.is_enable}, last_update={self.last_update})>"
    #     )
