from pydantic import BaseModel, constr, validator
import re

class UploadFile(BaseModel):
    filename: str
    content_type: str

class HealthStatus(BaseModel):
    status: str


"""
Translation schemas.

Pydantic models for request/response validation and serialization.
"""

from typing import Optional

from pydantic import BaseModel, Field, validator


class LanguageLocaleCreate(BaseModel):
    """Schema for creating a new language locale."""

    language: str = Field(..., min_length=1, max_length=192, description="Language name")
    language_code: str = Field(
        ...,
        min_length=5,
        max_length=5,
        description="Language code in format xx_XX",
    )
    language_name: str = Field(
        ..., min_length=1, max_length=384, description="Full language name"
    )
    is_enable: int = Field(1, ge=0, le=1, description="Enable status (0 or 1)")

    @validator("language_code")
    def validate_language_code(cls, v):
        """Validate language code format."""
        import re

        if not re.match(r"^[a-z]{2}_[A-Z]{2}$", v):
            raise ValueError(
                "Language code must be in format xx_XX (e.g., en_US, es_ES)"
            )
        return v

    @validator("language", "language_name")
    def validate_not_empty(cls, v):
        """Validate string fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    class Config:
        """Pydantic config."""

        schema_extra = {
            "example": {
                "language": "Spanish",
                "language_code": "es_ES",
                "language_name": "Español",
                "is_enable": 1,
            }
        }


class LanguageLocaleResponse(BaseModel):
    """Schema for language locale response."""

    id: int
    language: str
    language_code: str
    language_name: str
    is_enable: int

    class Config:
        """Pydantic config."""

        orm_mode = True


class TranslationUploadResponse(BaseModel):
    """Schema for translation upload response."""

    message: str
    translations_processed: int
    po_file_path: Optional[str] = None

    class Config:
        """Pydantic config."""

        schema_extra = {
            "example": {
                "message": "Translations uploaded successfully for Spanish",
                "translations_processed": 150,
                "po_file_path": "/locales/es_ES/LC_MESSAGES/salesplaypos.po",
            }
        }


class POGenerationResponse(BaseModel):
    """Schema for PO file generation response."""

    message: str

    class Config:
        """Pydantic config."""

        schema_extra = {
            "example": {
                "message": "PO file created for Spanish",
            }
        }


class CompilationResponse(BaseModel):
    """Schema for PO compilation response."""

    status: str
    message: str
    mo_path: str
    output: str

    class Config:
        """Pydantic config."""

        schema_extra = {
            "example": {
                "status": "success",
                "message": "Compiled salesplaypos.po → salesplaypos.mo",
                "mo_path": "/locales/es_ES/LC_MESSAGES/salesplaypos.mo",
                "output": "Compilation successful",
            }
        }