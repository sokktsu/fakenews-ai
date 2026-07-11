"""
OCR Service — Tesseract + EasyOCR fallback
"""
import os
import pytesseract
# On Windows point at the local install; on Linux (HF Space) tesseract is on PATH.
_WIN_TESSERACT = r"C:\C Codes (Apps)\Tesseract-OCR\tesseract.exe"
if os.path.exists(_WIN_TESSERACT):
    pytesseract.pytesseract.tesseract_cmd = _WIN_TESSERACT
from loguru import logger


def extract_text_from_image(image_path: str) -> str:
    """Try Tesseract first, fall back to EasyOCR."""
    text = _tesseract_ocr(image_path)
    if not text or len(text.strip()) < 10:
        text = _easyocr(image_path)
    return (text or "").strip()


def _tesseract_ocr(image_path: str) -> str:
    try:
        import pytesseract
        from PIL import Image
        img  = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang="eng")
        return text
    except Exception as e:
        logger.warning(f"Tesseract OCR failed: {e}")
        return ""


def _easyocr(image_path: str) -> str:
    try:
        import easyocr
        reader  = easyocr.Reader(["en"], gpu=False, verbose=False)
        results = reader.readtext(image_path, detail=0)
        return " ".join(results)
    except Exception as e:
        logger.warning(f"EasyOCR failed: {e}")
        return ""
