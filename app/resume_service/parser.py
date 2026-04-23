"""PDF text extraction logic for resume files."""

from typing import List


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract UTF-8 text content from a PDF using PyMuPDF.

    Raises:
        RuntimeError: If PyMuPDF is unavailable.
        ValueError: If the PDF is empty or unreadable.
    """
    try:
        import fitz
    except ImportError as exc:  # pragma: no cover - dependency check
        raise RuntimeError("PyMuPDF is not installed.") from exc

    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as document:
            pages: List[str] = []
            for page in document:
                pages.append(page.get_text("text") or "")
        text = "\n".join(pages).strip()
        if not text:
            raise ValueError("No extractable text found in the PDF.")
        return text
    except Exception as exc:
        raise ValueError("Failed to parse resume PDF.") from exc
