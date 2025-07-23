import re
import os
import sys
from datetime import datetime

po_file_path     = 'salesplaypos.po'                     
report_file_path = 'trailing_spaces_report.txt'         

# Regex to match msgid/msgstr lines ending with one or more spaces before the closing quote
TRAILING_SPACE_RE = re.compile(
    r'^(?P<key>msg(?:id|str))\s+"(?P<body>.*?)(?P<trail>\s+)"\s*$'
)

def scan_po_content(po_content):
    """
    Scan the .po content for trailing spaces in msgid/msgstr lines.
    Returns a list of dicts with: line_no, key, full_line, body, trail_len.
    """
    findings = []
    for idx, line in enumerate(po_content.splitlines(), start=1):
        m = TRAILING_SPACE_RE.match(line)
        if m:
            findings.append({
                'line_no':  idx,
                'key':       m.group('key'),
                'full_line': line,
                'body':      m.group('body'),
                'trail_len': len(m.group('trail')),
            })
    return findings

def write_text_report(path, findings, source_path):

    out_dir = os.path.dirname(path)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(path, 'w', encoding='utf-8') as rpt:
        rpt.write(f"Trailing‑Spaces Report for: {source_path}\n")
        rpt.write(f"Generated: {now}\n")
        rpt.write(f"Total issues found: {len(findings)}\n")
        rpt.write("=" * 60 + "\n\n")
        for item in findings:
            rpt.write(f"Line {item['line_no']}: {item['key']}\n")
            rpt.write(f"  Original: {item['full_line']!r}\n")
            rpt.write(f"  Text    : \"{item['body']}\"\n")
            rpt.write("-" * 60 + "\n")
    print(f"⚠️ Found {len(findings)} issue(s). Report written to: {path}")

def main():
    # Read the .po file
    try:
        with open(po_file_path, 'r', encoding='utf-8') as f:
            po_content = f.read()
    except FileNotFoundError:
        print(f"❌ Error: .po file not found at '{po_file_path}'")
        sys.exit(1)

    # Scan for trailing-space issues
    findings = scan_po_content(po_content)

    # If none found, exit; otherwise write the report
    if not findings:
        print("✅ No trailing‑space issues found in msgid/msgstr lines.")
        sys.exit(0)

    write_text_report(report_file_path, findings, po_file_path)

if __name__ == '__main__':
    main()
