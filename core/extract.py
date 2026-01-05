from __future__ import annotations
from pathlib import Path
import pdfplumber
from docx import Document

def extract_text_from_pdf(path: str) -> str:
    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            t = t.strip()
            if t:
                text_parts.append(t)
    return "\n\n".join(text_parts).strip()

def extract_text_from_docx(path: str) -> str:
    doc = Document(path)
    parts = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
    return "\n".join(parts).strip()

def extract_resume_text(path: str) -> str:
    ext = Path(path).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(path)
    if ext == ".docx":
        return extract_text_from_docx(path)
    raise ValueError(f"Unsupported file type: {ext}")

def needs_ocr(text: str) -> bool:
    """
    Simple heuristic: if extracted text is tiny, it might be a scanned PDF.
    """
    return (not text) or len(text.strip()) < 200
