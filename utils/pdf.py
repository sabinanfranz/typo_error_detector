# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Optional

import os
from typing import Generator, Tuple
import fitz  # PyMuPDF

# OCR 모듈/경로 준비
try:
    import pytesseract
    from PIL import Image

    if os.name == "nt":
        default = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.exists(default):
            pytesseract.pytesseract.tesseract_cmd = default
        else:
            from shutil import which
            exe = which("tesseract")
            if exe:
                pytesseract.pytesseract.tesseract_cmd = exe
    OCR_AVAILABLE = True
except Exception:
    pytesseract = None
    Image = None
    OCR_AVAILABLE = False


def extract_pages(pdf_path: str, use_ocr: bool = False, ocr_threshold: int = 50) -> Generator[Tuple[int, str, bool], None, None]:
    """
    페이지별 텍스트 추출 제너레이터
    Yields: (page_number, text, is_ocr_used)
    """
    doc = None
    try:
        doc = fitz.open(pdf_path)
        for idx in range(len(doc)):
            page = doc.load_page(idx)
            page_no = idx + 1

            text = page.get_text("text") or ""
            is_ocr = False

            if use_ocr and OCR_AVAILABLE and _need_ocr(text, ocr_threshold):
                try:
                    ocr_text = _ocr_page(page, lang="kor+eng", base_dpi=180)
                    if len(ocr_text.strip()) > len(text.strip()):
                        text = ocr_text
                        is_ocr = True
                except Exception as e:
                    # 실패 시 기본 텍스트 사용
                    print(f"페이지 {page_no} OCR 실패: {e}")

            yield page_no, text, is_ocr
    finally:
        if doc is not None:
            doc.close()


def _need_ocr(text: str, threshold: int) -> bool:
    """문자 수 임계치 기반 OCR 필요 여부"""
    return len((text or "").strip()) < int(threshold)


def _page_pixmap(page, dpi: int, alpha: bool = False):
    """PNG 인코딩 없이 Pixmap 생성 (빠름)"""
    scale = max(0.5, dpi / 72.0)
    mat = fitz.Matrix(scale, scale)
    return page.get_pixmap(matrix=mat, alpha=alpha)


def _pixmap_to_pil(pix) -> Optional[Image.Image]:
    if Image is None:
        return None
    if pix.alpha:
        pix = fitz.Pixmap(fitz.csRGB, pix)
    return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

def _ocr_page(page, lang: str = "kor+eng", base_dpi: int = 180) -> str:
    """OCR 실행 (해상도 적응)"""
    if not (OCR_AVAILABLE and pytesseract and Image):
        return ""

    dpi = base_dpi
    for _ in range(3):  # 과도한 해상도일 때 단계적으로 낮춤
        pix = _page_pixmap(page, dpi=dpi, alpha=False)
        mp = (pix.width * pix.height) / 1_000_000
        if mp <= 12:
            break
        dpi = max(96, int(dpi * 0.75))

    img = _pixmap_to_pil(pix)
    if img is None:
        return ""
    return pytesseract.image_to_string(img, lang=lang)
