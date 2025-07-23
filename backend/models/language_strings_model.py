from sqlalchemy import Column, BigInteger, String, Integer, TIMESTAMP, Text,func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class LanguageString(Base):
    __tablename__ = 'language_strings'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    msgid = Column(String(512, collation="utf8mb4_bin"), nullable=False, unique=True)
    msgstr = Column(Text(collation="utf8mb4_general_ci"))
    en_US = Column(Integer, default=0, comment='English')
    es_ES = Column(Integer, default=0, comment='Spanish')
    fi_FI = Column(Integer, default=0, comment='Filipino')
    ar_AE = Column(Integer, default=0, comment='Arabic')
    fr_FR = Column(Integer, default=0, comment='French')
    hi_IN = Column(Integer, default=0, comment='Hindi')
    km_KH = Column(Integer, default=0, comment='Khmer')
    ru_RU = Column(Integer, default=0, comment='Russian')
    zh_CN = Column(Integer, default=0, comment='Chinese')
    ja_JP = Column(Integer, default=0, comment='Japanese')
    sv_SE = Column(Integer, default=0, comment='Swedish')
    de_DE = Column(Integer, default=0, comment='German')
    az_AZ = Column(Integer, default=0, comment='Azerbaijani')
    uz_UZ = Column(Integer, default=0, comment='Uzbek')
    si_SI = Column(Integer, default=0, comment='Sinhala')
    last_update = Column(TIMESTAMP, default=func.now(), onupdate=func.now(), nullable=True)