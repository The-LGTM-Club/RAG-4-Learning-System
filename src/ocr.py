from __future__ import annotations

from pathlib import Path

from loguru import logger

from src.config import Settings
from src.filters import clean_text


def _load_ocr_dependencies():
    try:
        import fitz
        from PIL import Image
        import pytesseract
    except ImportError as exc:
        raise RuntimeError(
            "OCR support requires PyMuPDF, Pillow, and pytesseract. "
            "Install the Python dependencies for this project first."
        ) from exc
    return fitz, Image, pytesseract


def extract_page_texts(
    path: Path,
    page_numbers: list[int],
    settings: Settings,
) -> dict[int, str]:
    if not page_numbers:
        return {}

    fitz, Image, pytesseract = _load_ocr_dependencies()
    if settings.ocr_tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = settings.ocr_tesseract_cmd

    zoom = settings.ocr_dpi / 72.0
    ocr_texts: dict[int, str] = {}

    try:
        with fitz.open(path) as pdf:
            for page_number in sorted(set(page_numbers)):
                page = pdf.load_page(page_number)
                pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
                image = Image.frombytes(
                    "RGB",
                    (pixmap.width, pixmap.height),
                    pixmap.samples,
                )
                text = pytesseract.image_to_string(
                    image,
                    lang=settings.ocr_language,
                )
                ocr_texts[page_number] = clean_text(text)
    except pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError(
            "Tesseract OCR is not installed or not available in PATH. "
            "Install Tesseract and set NOTEBOOKLM_OCR_TESSERACT_CMD if needed."
        ) from exc
    except Exception as exc:
        raise RuntimeError(f"Failed to OCR PDF pages from {path}") from exc

    logger.info(
        "OCR extracted text from {} pages in {}.",
        len(ocr_texts),
        path.name,
    )
    return ocr_texts
