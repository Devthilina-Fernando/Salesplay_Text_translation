import re
from sqlalchemy import create_engine, MetaData, Table, select, update
from sqlalchemy.dialects.mysql import insert

import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)
from backend.config.config import Config

from datetime import datetime

def safe_unescape(s):
    """Safely unescape string while handling empty strings and special cases"""
    if not s:
        return s
        
    try:
        # Handle escaped characters
        return s.encode('utf-8').decode('unicode_escape')
    except UnicodeDecodeError:
        # Fallback for problematic escape sequences
        return s.replace('\\', '\\\\')

def parse_po_content(po_content):
    """Parse PO content and extract msgid/msgstr pairs"""
    entries = []
    # Improved regex to handle multi-line strings and various quoting styles
    pattern = re.compile(
        r'msgid\s+(?:"(.*?)"|\'(.*?)\')\s+msgstr\s+(?:"(.*?)"|\'(.*?)\')',
        re.DOTALL
    )
    
    for match in pattern.finditer(po_content):
        # Extract msgid from either double or single quoted group
        msgid = match.group(1) or match.group(2) or ""
        # Extract msgstr from either double or single quoted group
        msgstr = match.group(3) or match.group(4) or ""
        
        # Unescape special characters safely
        msgid = safe_unescape(msgid)
        msgstr = safe_unescape(msgstr)
        
        # Skip header entry (empty msgid)
        if not msgid:
            continue
            
        # Truncate msgid if too long
        if len(msgid) > 512:
            msgid = msgid[:512]
            
        entries.append((msgid, msgstr))
    
    return entries

def process_po_entries(entries):
    """Identify duplicates and separate unique entries"""
    seen = {}
    unique_entries = []
    duplicates = []
    duplicate_count = 0
    
    for idx, (msgid, msgstr) in enumerate(entries):
        if msgid in seen:
            duplicates.append({
                "original_index": seen[msgid],
                "duplicate_index": idx + 1,
                "msgid": msgid,
                "msgstr": msgstr
            })
            duplicate_count += 1
        else:
            seen[msgid] = idx + 1
            unique_entries.append((msgid, msgstr))
    
    return unique_entries, duplicates, duplicate_count

def write_duplicates_report(duplicates, filename):
    """Write duplicates information to a text file"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"DUPLICATE ENTRIES REPORT\n")
        f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total duplicates found: {len(duplicates)}\n\n")
        
        for dup in duplicates:
            f.write(f"DUPLICATE ENTRY #{dup['duplicate_index']}\n")
            f.write(f"Original at position: {dup['original_index']}\n")
            f.write(f"msgid: {dup['msgid']}\n")
            f.write(f"msgstr: {dup['msgstr']}\n")
            f.write("-" * 50 + "\n\n")

def write_summary_report(total_records, unique_count, duplicate_count, filename):
    """Write processing summary to a text file"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("PO FILE PROCESSING SUMMARY\n")
        f.write("=" * 50 + "\n")
        f.write(f"Processing completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Total records in PO file: {total_records}\n")
        f.write(f"Duplicate records found: {duplicate_count}\n")
        f.write(f"Unique records processed: {unique_count}\n")
        f.write(f"Records uploaded to database: {unique_count}\n")
        f.write("\n" + "=" * 50 + "\n")
        f.write("NOTE: Only the first occurrence of each msgid was inserted into the database.\n")
        f.write("Duplicates were skipped but preserved in a separate report file.\n")

def upsert_language_strings(entries):
    """Upsert entries into database using SQLAlchemy"""
    # Create database engine from config
    engine = create_engine(
        Config.SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,
        connect_args={
            "charset": "utf8mb4",
            "collation": "utf8mb4_general_ci"
        }
    )
    
    metadata = MetaData()
    # Reflect language_strings table structure
    language_strings = Table(
        'language_strings',
        metadata,
        autoload_with=engine
    )
    
    with engine.connect() as connection:
        # Start transaction
        trans = connection.begin()
        try:
            for msgid, msgstr in entries:
                # Create upsert statement
                stmt = insert(language_strings).values(
                    msgid=msgid,
                    msgstr=msgid
                )
                
                # Update on duplicate key
                update_stmt = stmt.on_duplicate_key_update(
                    msgid=stmt.inserted.msgid
                )
                
                # Execute the statement
                connection.execute(update_stmt)
            
            # Commit transaction
            trans.commit()
            print(f"Successfully processed {len(entries)} records")
            
        except Exception as e:
            trans.rollback()
            print(f"Database operation failed: {e}")
            raise


if __name__ == "__main__":
    # Read PO file content
    # po_file_path = '600/600.po' 
    po_file_path ='salesplaypos.po'
    with open(po_file_path, 'r', encoding='utf-8') as f:
        po_content = f.read()
    
    # Parse PO content
    all_entries = parse_po_content(po_content)
    total_records = len(all_entries)
    
    # Process entries to identify duplicates
    unique_entries, duplicates, duplicate_count = process_po_entries(all_entries)
    unique_count = len(unique_entries)
    
    # Generate report filenames with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = "po_processing_reports"
    os.makedirs(report_dir, exist_ok=True)
    
    duplicates_report = os.path.join(report_dir, f"duplicates_report_{timestamp}.txt")
    summary_report = os.path.join(report_dir, f"processing_summary_{timestamp}.txt")
    
    # Write reports if duplicates found
    if duplicate_count > 0:
        write_duplicates_report(duplicates, duplicates_report)
        print(f"Found {duplicate_count} duplicates. Report saved to: {duplicates_report}")
    
    # Write summary report
    write_summary_report(total_records, unique_count, duplicate_count, summary_report)
    print(f"Processing summary saved to: {summary_report}")
    
    # Upsert unique entries to database
    if unique_count > 0:
        upsert_language_strings(unique_entries)
    else:
        print("No unique records to process")

    # Print final summary to console
    print("\nPROCESSING SUMMARY")
    print("==================")
    print(f"Total records in PO file: {total_records}")
    print(f"Duplicate records found: {duplicate_count}")
    print(f"Unique records processed: {unique_count}")
    print(f"Records uploaded to database: {unique_count}")
    if duplicate_count > 0:
        print(f"\nNote: {duplicate_count} duplicate records were skipped. First occurrence was retained.")