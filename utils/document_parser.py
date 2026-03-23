import re
from datetime import datetime
from typing import List, Dict, Tuple
import pdfplumber
from docx import Document as DocxDocument
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(filepath: str) -> str:
    """Extract text from PDF file."""
    text = ""
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
                text += "\n"
    except Exception as e:
        raise ValueError(f"Error reading PDF: {str(e)}")
    return text

def extract_text_from_docx(filepath: str) -> str:
    """Extract text from DOCX file."""
    text = ""
    try:
        doc = DocxDocument(filepath)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        raise ValueError(f"Error reading DOCX: {str(e)}")
    return text

def extract_text_from_txt(filepath: str) -> str:
    """Extract text from TXT file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise ValueError(f"Error reading TXT: {str(e)}")

def extract_text(filepath: str, file_type: str) -> str:
    """Extract text from document based on file type."""
    if file_type == 'pdf':
        return extract_text_from_pdf(filepath)
    elif file_type == 'docx':
        return extract_text_from_docx(filepath)
    elif file_type == 'txt':
        return extract_text_from_txt(filepath)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

def parse_date(date_str: str) -> str:
    """Parse various date formats and return ISO format (YYYY-MM-DD)."""
    if not date_str:
        return None
    
    date_str = date_str.strip()
    
    # List of date patterns to try (order matters - try more specific patterns first)
    patterns = [
        # ISO format: 2025-12-31
        (r'^(\d{4})-(\d{1,2})-(\d{1,2})', lambda m: f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"),
        # US format: 12/31/2025 or 12-31-2025
        (r'^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$', lambda m: f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"),
        # Text format: December 31, 2025 or Dec 31, 2025
        (r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (\d{1,2}),? (\d{4})$',
         lambda m: datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}", "%b %d %Y").strftime("%Y-%m-%d")),
    ]
    
    for pattern, formatter in patterns:
        match = re.search(pattern, date_str, re.IGNORECASE)
        if match:
            try:
                result = formatter(match)
                # Validate the date
                datetime.strptime(result, "%Y-%m-%d")
                return result
            except (ValueError, AttributeError):
                continue
    
    return None

def split_entries_by_date(text: str) -> List[Dict[str, str]]:
    """
    Parse text and split into entries by detected dates.
    Returns list of dicts with 'date' and 'content' keys.
    """
    entries = []
    lines = text.split('\n')
    
    current_date = None
    current_content = []
    
    for line in lines:
        stripped = line.strip()
        
        # Try to detect a date at the start of the line
        if stripped:  # Only check non-empty lines
            parsed_date = parse_date(stripped)
            
            if parsed_date:
                # We found a new date
                if current_date and current_content:
                    # Save the previous entry
                    content_text = '\n'.join(current_content).strip()
                    if content_text:  # Only save if there's content
                        entries.append({
                            'date': current_date,
                            'content': content_text
                        })
                
                current_date = parsed_date
                current_content = []
                continue
        
        # This is content for the current entry
        if current_date:
            current_content.append(line)
    
    # Don't forget the last entry
    if current_date and current_content:
        content_text = '\n'.join(current_content).strip()
        if content_text:  # Only save if there's content
            entries.append({
                'date': current_date,
                'content': content_text
            })
    
    return entries

def validate_entries(entries: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], List[str]]:
    """
    Validate parsed entries and return valid entries and error messages.
    """
    valid_entries = []
    errors = []
    
    for i, entry in enumerate(entries):
        date = entry.get('date', '').strip()
        content = entry.get('content', '').strip()
        
        # Validate date
        if not date:
            errors.append(f"Entry {i + 1}: No date found. Please make sure each entry starts with a date.")
            continue
        
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            errors.append(f"Entry {i + 1}: Could not recognize the date format '{date}'. Use formats like: 2025-12-31, 12/31/2025, or December 31, 2025")
            continue
        
        # Validate content
        if not content:
            errors.append(f"Entry {i + 1} (dated {date}): No content found. Please add text after the date.")
            continue
        
        if len(content) > 10000:
            errors.append(f"Entry {i + 1} (dated {date}): Content is too long ({len(content)} characters). Maximum is 10,000 characters.")
            continue
        
        valid_entries.append({
            'date': date,
            'content': content,
            'title': f"Entry - {date}"  # Generate a simple title
        })
    
    return valid_entries, errors
