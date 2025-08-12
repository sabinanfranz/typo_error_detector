# -*- coding: utf-8 -*-
import unicodedata
import re
from typing import List

def normalize_text(text: str) -> str:
    """
    텍스트를 정규화합니다.
    
    Args:
        text: 정규화할 텍스트
        
    Returns:
        정규화된 텍스트
    """
    if not text:
        return ""
    
    # Unicode NFKC 정규화
    text = unicodedata.normalize("NFKC", text)
    
    # 제어 문자 제거
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # 소프트 하이픈 제거
    text = text.replace('\u00AD', '')
    
    # 제로 너비 문자들 제거
    text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)
    
    # 연속 공백을 하나로 축약
    text = re.sub(r'[ \t\u00A0]+', ' ', text)
    
    # 연속 줄바꿈을 하나로 축약
    text = re.sub(r'\n+', '\n', text)
    
    return text.strip()

def split_sentences(text: str) -> List[str]:
    """
    텍스트를 문장 단위로 분리합니다.
    
    Args:
        text: 분리할 텍스트
        
    Returns:
        문장 리스트
    """
    if not text:
        return []
    
    # kss 라이브러리 사용 시도
    try:
        import kss
        sentences = kss.split_sentences(text)
        return [s.strip() for s in sentences if s.strip()]
    except ImportError:
        # kss가 없으면 간단한 정규식으로 분리
        return _fallback_sentence_split(text)
    except Exception:
        # kss 오류 시 fallback 사용
        return _fallback_sentence_split(text)

def _fallback_sentence_split(text: str) -> List[str]:
    """kss 실패 시 사용하는 간단한 문장 분리."""
    # 한국어 문장 종결 패턴
    patterns = [
        r'[.!?。！？]\s*',  # 일반 문장 부호
        r'[가-힣]다\s+',   # 한국어 동사 종결
        r'[가-힣]요\s+',   # 한국어 종결어미
        r'[가-힣]네\s+',   # 한국어 종결어미
        r'[가-힣]어\s+',   # 한국어 종결어미
        r'[가-힣]아\s+',   # 한국어 종결어미
        r'\n+',            # 줄바꿈
    ]
    
    # 패턴으로 분리
    sentences = [text]
    for pattern in patterns:
        new_sentences = []
        for sentence in sentences:
            parts = re.split(pattern, sentence)
            new_sentences.extend(parts)
        sentences = new_sentences
    
    # 빈 문장 제거 및 정리
    return [s.strip() for s in sentences if s.strip()]

def visible_korean_ratio(text: str) -> float:
    """
    텍스트에서 한글 문자의 비율을 계산합니다.
    
    Args:
        text: 분석할 텍스트
        
    Returns:
        한글 비율 (0.0 ~ 1.0)
    """
    if not text:
        return 0.0
    
    # 한글 유니코드 범위: AC00-D7A3
    korean_chars = sum(1 for ch in text if '\uac00' <= ch <= '\ud7a3')
    
    # 공백이 아닌 가시 문자 수
    visible_chars = sum(1 for ch in text if not ch.isspace())
    
    return korean_chars / visible_chars if visible_chars > 0 else 0.0

def filter_korean_centric_lines(text: str, min_ratio: float = 0.3) -> str:
    """
    한글 중심이 아닌 라인을 필터링합니다.
    
    Args:
        text: 필터링할 텍스트
        min_ratio: 최소 한글 비율
        
    Returns:
        필터링된 텍스트
    """
    if not text:
        return ""
    
    lines = text.split('\n')
    filtered_lines = []
    
    for line in lines:
        if visible_korean_ratio(line) >= min_ratio:
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)

def remove_code_blocks(text: str) -> str:
    """
    코드 블록을 제거합니다.
    
    Args:
        text: 원본 텍스트
        
    Returns:
        코드 블록이 제거된 텍스트
    """
    # 코드 블록 패턴 (```로 둘러싸인 부분)
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    
    # 인라인 코드 (`로 둘러싸인 부분)
    text = re.sub(r'`[^`]+`', '', text)
    
    # 프로그래밍 언어 키워드가 많은 라인 제거
    lines = text.split('\n')
    filtered_lines = []
    
    for line in lines:
        # 프로그래밍 키워드 개수 계산
        code_keywords = len(re.findall(r'\b(if|else|for|while|def|class|import|from|return|print|var|let|const|function)\b', line, re.IGNORECASE))
        
        # 키워드가 2개 이상이면 코드 라인으로 간주
        if code_keywords < 2:
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)
