import fitz  # PyMuPDF
import re

def read_pdf(file_path: str) -> str:
    """Reads text content from a PDF file."""
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
        return ""

def read_text(file_path: str) -> str:
    """Reads text content from a plain text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading text file {file_path}: {e}")
        return ""

def clean_text(text: str) -> str:
    """Performs basic text cleaning."""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Add more cleaning steps if needed (e.g., removing headers/footers, special characters)
    return text

def process_document(file_path: str) -> str:
    """Reads and cleans text from a supported document file."""
    text = ""
    if file_path.lower().endswith('.pdf'):
        text = read_pdf(file_path)
    elif file_path.lower().endswith('.txt'):
        text = read_text(file_path)
    # Add support for other formats like JSON if needed
    else:
        print(f"Unsupported file format: {file_path}")
        return ""

    cleaned_text = clean_text(text)
    return cleaned_text