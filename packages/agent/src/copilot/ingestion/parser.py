"""Extract plain text from uploaded files (PDF, TXT, MD)."""

import io
import logging

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}


class UnsupportedFileError(ValueError):
    pass


def parse_file(filename: str, data: bytes) -> str:
    """Return the plain text content of an uploaded file."""
    name = filename.lower()
    if name.endswith(".pdf"):
        return _parse_pdf(data)
    if name.endswith((".txt", ".md")):
        return data.decode("utf-8", errors="replace")
    raise UnsupportedFileError(
        f"Unsupported file type: {filename}. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
    )


def _parse_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception as e:
            logger.warning("Failed to extract a PDF page: %s", e)
    text = "\n\n".join(pages).strip()
    if not text:
        raise UnsupportedFileError(
            "No extractable text found in PDF (it may be a scanned image)."
        )
    return text
