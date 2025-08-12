# -*- coding: utf-8 -*-
import fitz  # PyMuPDF
from typing import Generator, Tuple, Optional
import io

# OCR 관련 모듈 import 시도
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    pytesseract = None
    Image = None

def extract_pages(pdf_path: str, use_ocr: bool = False, ocr_threshold: int = 50) -> Generator[Tuple[int, str, bool], None, None]:
    """
    PDF에서 페이지별 텍스트를 추출합니다.
    
    Args:
        pdf_path: PDF 파일 경로
        use_ocr: OCR 사용 여부
        ocr_threshold: OCR 트리거 문자 수 임계값
    
    Yields:
        (page_number, text, is_ocr_used)
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"PDF 파일 열기 실패: {e}")
        return
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        page_number = page_num + 1
        
        # 기본 텍스트 추출
        text = page.get_text("text")
        
        # OCR 필요 여부 판단
        is_ocr = False
        if use_ocr and OCR_AVAILABLE and _need_ocr(text, page, ocr_threshold):
            try:
                text = _ocr_page(page)
                is_ocr = True
            except Exception as e:
                print(f"페이지 {page_number} OCR 실패: {e}")
        
        yield page_number, text, is_ocr
    
    doc.close()

def _need_ocr(text: str, page, threshold: int) -> bool:
    """OCR이 필요한지 판단합니다."""
    # 텍스트가 너무 적거나 임계값 미만인 경우
    if len(text.strip()) < threshold:
        return True
    
    # 페이지 면적 대비 텍스트 밀도가 낮은 경우
    page_area = page.rect.width * page.rect.height
    text_density = len(text) / page_area if page_area > 0 else 0
    
    return text_density < 0.001  # 임계값

def _ocr_page(page) -> str:
    """페이지를 OCR로 처리합니다."""
    if not OCR_AVAILABLE:
        raise ImportError("OCR 모듈이 설치되지 않았습니다")
    
    # 페이지를 이미지로 렌더링
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2배 확대
    img_data = pix.tobytes("png")
    
    # PIL Image로 변환
    img = Image.open(io.BytesIO(img_data))
    
    # OCR 실행 (한국어 설정)
    text = pytesseract.image_to_string(img, lang='kor+eng')
    
    return text
