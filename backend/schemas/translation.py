from pydantic import BaseModel, constr, validator
import re

class LanguageLocaleCreate(BaseModel):
    language: str
    language_code: str
    language_name: str
    is_enable: int = 1

    @validator('language_code')
    def validate_language_code(cls, v):
        if not re.match(r'^[a-z]{2}_[A-Z]{2}$', v):
            raise ValueError('Language code must be in format: ll_CC (e.g., en_US)')
        return v
    
class UploadFile(BaseModel):
    filename: str
    content_type: str