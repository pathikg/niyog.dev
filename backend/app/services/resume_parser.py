import base64
import hashlib
import io

import fitz  # pymupdf
from docx import Document


def parse_pdf_to_text(file_bytes: bytes) -> str:
    """Extract text from PDF using pymupdf."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n".join(text_parts)


def parse_pdf_to_images(file_bytes: bytes) -> list[str]:
    """Convert PDF pages to base64-encoded PNG images (for vision models)."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    images = []
    for page in doc:
        pix = page.get_pixmap(dpi=200)
        img_bytes = pix.tobytes("png")
        b64 = base64.b64encode(img_bytes).decode()
        images.append(b64)
    doc.close()
    return images


def parse_docx_to_text(file_bytes: bytes) -> str:
    """Extract text from DOCX file."""
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def compute_file_hash(file_bytes: bytes) -> str:
    """SHA-256 hash of the file bytes."""
    return f"sha256:{hashlib.sha256(file_bytes).hexdigest()}"


def detect_file_type(filename: str) -> str:
    """Detect file type from extension."""
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return "pdf"
    elif lower.endswith(".docx"):
        return "docx"
    else:
        raise ValueError(f"Unsupported file type: {filename}. Only PDF and DOCX are supported.")
