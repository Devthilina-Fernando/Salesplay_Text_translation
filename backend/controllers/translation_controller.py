import os
import re
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, NoSuchTableError
# from openai import OpenAI
from pydantic import BaseModel
from config.config import Config
from config.logger import logger
from models.language_local_model import LanguageLocale
from models.language_strings_model import LanguageString
from datetime import datetime
import time
from openai import AsyncOpenAI
import asyncio
from openai import AsyncOpenAI
from typing import List, Tuple

# os.environ.pop("SSL_CERT_FILE", None) 

# client = OpenAI(api_key=Config.OPENAI_API_KEY)
client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

class TranslationResult(BaseModel):
    translated_text: str


def get_zero_msgids(db: Session, lang_column: str) -> List[str]:
    try:
        logger.info(f"Getting zero msgids for: {lang_column}")
        if not hasattr(LanguageString, lang_column):
            error_msg = f"Invalid language column: {lang_column}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        column_attr = getattr(LanguageString, lang_column)
        query = db.query(LanguageString.msgid).filter(column_attr == 0).order_by(LanguageString.id)
        return [row.msgid for row in query.all()]
    

    except NoSuchTableError:
        error_msg = f"Table '{LanguageString.__tablename__}' does not exist"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        logger.error(f"Error getting zero msgids: {str(e)}")
        raise


async def translate_msgids(db: Session, msgids: List[str], lang_name: str, lang_code: str) -> List[str]:
    logger.info(f"Translating {len(msgids)} strings to {lang_name}")
    translations = []
    batch_size = 500  # Adjust based on your needs
    max_concurrency = 20  # Max parallel requests
    
    # Define the system prompt
    system_prompt = (
        "You are a professional POS translator. Translate text while EXACTLY preserving: "
        "• Punctuation, numbers, symbols, and formatting\n"
        "NEVER add/remove quotes or other characters.\n"
        "Return ONLY the translated text."
        "\nSTRICTLY DO NOT ADD ANY UNWANTED PUNCTUATION MARKS APPART FROM THE GIVEN"
    )

    async def translate_text(text: str, client: AsyncOpenAI, semaphore: asyncio.Semaphore) -> str:
        async with semaphore:
            response = await client.responses.parse(
                model="gpt-4o-2024-08-06",
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Translate the following to {lang_name} exactly as requested:\n\n{text}"}
                ],
                text_format=TranslationResult,
            )
            return response.output_parsed.translated_text

    async def process_batch(batch_msgids: List[str]) -> Tuple[List[str], List[str]]:
        """Translate a batch and return (translations, failed_msgids)"""
        semaphore = asyncio.Semaphore(max_concurrency)
        async with AsyncOpenAI() as client:
            tasks = [translate_text(msgid, client, semaphore) for msgid in batch_msgids]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        batch_translations = []
        failed_msgids = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error translating '{batch_msgids[i]}': {str(result)}")
                batch_translations.append(batch_msgids[i])  # Use original on error
                failed_msgids.append(batch_msgids[i])
            else:
                batch_translations.append(result)
                print("###########@@@@@@@@@@@@@@@@@@@##############")
                print(batch_translations)
        
        # return batch_translations, failed_msgids
        return batch_translations
    # Process in batches
    for i in range(0, len(msgids), batch_size):
        batch = msgids[i:i + batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}/{(len(msgids)-1)//batch_size + 1}")
        
        # batch_translations, failed_msgids = await process_batch(batch)
        batch_translations = await process_batch(batch)
        translations.extend(batch_translations)
        
        # Update database for successful translations
        success_msgids = set(batch)
        if success_msgids:
            # Fetch records in bulk
            records = db.query(LanguageString).filter(
                LanguageString.msgid.in_(list(success_msgids))
            ).all()
            
            # Create lookup dictionary
            record_dict = {r.msgid: r for r in records}
            not_found = []
            
            for msgid in success_msgids:
                if msgid in record_dict:
                    setattr(record_dict[msgid], lang_code, 1)
                else:
                    not_found.append(msgid)
            
            # Commit bulk updates
            try:
                db.commit()
                for msgid in not_found:
                    logger.warning(f"No record found for msgid: '{msgid}'")
            except Exception as e:
                db.rollback()
                logger.error(f"Database commit failed: {str(e)}")
    
    return translations

#######################################################################################


def get_language_code_by_name(db: Session, language: str) -> Optional[str]:
    try:
        logger.info(f"Getting language code for: {language}")
        record = db.query(LanguageLocale.language_code).filter(
            LanguageLocale.language == language
        ).first()
        return record[0] if record else None
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise

import zoneinfo
tz = zoneinfo.ZoneInfo("Asia/Colombo")
now = datetime.now(tz)
ts = now.strftime("%Y-%m-%d %H:%M%z")

def update_po_content(
    existing_content: str,
    lang_name: str,
    new_msgids: List[str],
    new_translations: List[str]
) -> str:
    # Get current date
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Update the comment date
    existing_content = re.sub(
        r'(# date: )[\d-]+',
        f'\\g<1>{current_date}',
        existing_content
    )
    
    existing_content = re.sub(
        r'("PO-Revision-Date: )[\d:\s+-]+(?=\\n")',
        f'\\g<1>{ts}',
        existing_content
    )
    
    # Extract the body (after the header)
    header_end = existing_content.find('msgstr ""') + len('msgstr ""') + 1
    header = existing_content[:header_end]
    body = existing_content[header_end:]
    
    # Create lookup for existing translations
    existing_translations = {}
    for match in re.finditer(r'msgid "(.*?)"\nmsgstr "(.*?)"\n', body, re.DOTALL):
        msgid = match.group(1).replace('\\"', '"').replace('\\n', '\n')
        msgstr = match.group(2).replace('\\"', '"').replace('\\n', '\n')
        existing_translations[msgid] = msgstr
    
    # Ensure proper spacing at end of body
    if body and not body.endswith('\n\n'):
        body = body.rstrip() + '\n\n'
    
    # Add new translations (only for missing msgids)
    for msgid, translation in zip(new_msgids, new_translations):
        if msgid not in existing_translations:
            escaped_id = msgid.replace('"', '\\"').replace('\n', '\\n')
            escaped_tr = translation.replace('"', '\\"').replace('\n', '\\n')
            body += f'msgid "{escaped_id}"\n'
            body += f'msgstr "{escaped_tr}"\n\n'
    
    return header + body


# Original function remains for new file creation
def generate_po_content(lang_name: str,lang_code: str, msgids: List[str], translations: List[str]) -> str:
    logger.info("Generating PO content")
    content = [
        '# Autogenerated by SalesPlay Translate development',
        '#',
        f'# language: {lang_name}',
        f'# locale: {lang_code}',
        f'# date: {datetime.now().strftime("%Y-%m-%d")}',
        '#',
        'msgid ""',
        'msgstr ""',
        '"Project-Id-Version: SalesPlay POS Translation-0.000\\n"',
        f'"POT-Creation-Date: {ts}\\n"',
        f'"PO-Revision-Date: {ts}\\n"',
        '"Last-Translator: SalesPlay Team\\n"',
        '"Language-Team: SalesPlay (Pvt) Ltd <support@nvision.lk>\\n"',
        '"Language: en\\n"',
        '"MIME-Version: 1.0\\n"',
        '"Content-Type: text/plain; charset=UTF-8\\n"',
        '"Content-Transfer-Encoding: 8bit\\n"',
        '"Plural-Forms: nplurals=2; plural=n != 1;\\n"',
        '"X-Generator: Poedit 3.0.1\\n"',
        ''
    ]
    
    for msgid, msgstr in zip(msgids, translations):
        escaped_msgid = msgid.replace('"', '\\"').replace('\n', '\\n')
        escaped_msgstr = msgstr.replace('"', '\\"').replace('\n', '\\n')
        content.append(f'msgid "{escaped_msgid}"')
        content.append(f'msgstr "{escaped_msgstr}"\n')
    
    return "\n".join(content)