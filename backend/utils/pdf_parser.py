import io
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union
from PyPDF2 import PdfReader

logger = logging.getLogger("skillbridge.pdf_parser")


class PDFParsingError(Exception):
    """Exception raised when PDF parsing fails."""
    pass


def extract_text_from_pdf(
    pdf_source: Union[bytes, io.BytesIO, str, Path, Any]
) -> str:
    """
    Extract raw text from a PDF file source.

    Supports:
        - raw bytes
        - io.BytesIO stream
        - File path (str or Path)
        - FastAPI/Starlette UploadFile object (or objects with an async/sync .read() or .file attribute)

    Returns:
        Cleaned string containing extracted text from all pages.

    Raises:
        PDFParsingError: If file cannot be read, parsed, or contains no readable text.
    """
    try:
        stream: Optional[io.BytesIO] = None

        if isinstance(pdf_source, bytes):
            stream = io.BytesIO(pdf_source)
        elif isinstance(pdf_source, io.BytesIO):
            stream = pdf_source
            stream.seek(0)
        elif isinstance(pdf_source, (str, Path)):
            path = Path(pdf_source)
            if not path.exists() or not path.is_file():
                raise PDFParsingError(f"PDF file not found at path: {pdf_source}")
            with open(path, "rb") as f:
                stream = io.BytesIO(f.read())
        elif hasattr(pdf_source, "file") and hasattr(pdf_source.file, "read"):
            # FastAPI / Starlette UploadFile
            pdf_source.file.seek(0)
            content = pdf_source.file.read()
            if isinstance(content, str):
                content = content.encode("utf-8")
            stream = io.BytesIO(content)
        elif hasattr(pdf_source, "read"):
            # Generic file-like object
            content = pdf_source.read()
            if isinstance(content, str):
                content = content.encode("utf-8")
            stream = io.BytesIO(content)
        else:
            raise PDFParsingError(f"Unsupported PDF input type: {type(pdf_source)}")

        reader = PdfReader(stream)

        if reader.is_encrypted:
            try:
                # Attempt decrypt with empty password
                reader.decrypt("")
            except Exception as e:
                raise PDFParsingError(f"PDF is encrypted and cannot be opened: {str(e)}")

        extracted_pages = []
        for page_idx, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text()
                if page_text:
                    extracted_pages.append(page_text.strip())
            except Exception as page_err:
                logger.warning(f"Failed to extract text from page {page_idx + 1}: {page_err}")

        full_text = "\n\n".join(extracted_pages).strip()

        if not full_text:
            logger.warning("No readable text found in PDF (it might be image-based or scanned).")

        return full_text

    except PDFParsingError:
        raise
    except Exception as e:
        logger.error(f"Error while parsing PDF: {e}", exc_info=True)
        raise PDFParsingError(f"Failed to parse PDF document: {str(e)}") from e


def parse_pdf_resume(
    pdf_source: Union[bytes, io.BytesIO, str, Path, Any]
) -> Dict[str, Any]:
    """
    Parse a PDF resume, returning extracted text alongside document metadata.

    Returns:
        Dict with keys:
            - text: str
            - page_count: int
            - metadata: dict (title, author, producer, etc.)
            - character_count: int
            - word_count: int
    """
    try:
        # Determine stream for metadata extraction
        if isinstance(pdf_source, bytes):
            stream = io.BytesIO(pdf_source)
        elif isinstance(pdf_source, io.BytesIO):
            stream = pdf_source
            stream.seek(0)
        elif isinstance(pdf_source, (str, Path)):
            with open(pdf_source, "rb") as f:
                stream = io.BytesIO(f.read())
        elif hasattr(pdf_source, "file"):
            pdf_source.file.seek(0)
            stream = io.BytesIO(pdf_source.file.read())
        elif hasattr(pdf_source, "read"):
            stream = io.BytesIO(pdf_source.read())
        else:
            raise PDFParsingError(f"Unsupported PDF input type: {type(pdf_source)}")

        reader = PdfReader(stream)
        page_count = len(reader.pages)
        raw_metadata = reader.metadata or {}
        meta_clean = {
            str(k).replace("/", ""): str(v)
            for k, v in raw_metadata.items()
            if v is not None
        }

        text = extract_text_from_pdf(stream)
        words = text.split()

        return {
            "text": text,
            "page_count": page_count,
            "metadata": meta_clean,
            "character_count": len(text),
            "word_count": len(words),
        }
    except Exception as e:
        raise PDFParsingError(f"Resume PDF parsing failed: {str(e)}") from e
