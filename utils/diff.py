# -*- coding: utf-8 -*-
import difflib
from typing import List, Tuple

def simple_diff(original: str, corrected: str) -> str:
    """
    두 텍스트 간의 간단한 diff를 생성합니다.
    
    Args:
        original: 원본 텍스트
        corrected: 교정된 텍스트
        
    Returns:
        diff 문자열
    """
    if not corrected:
        return ""
    
    if original == corrected:
        return ""
    
    # SequenceMatcher로 차이점 분석
    matcher = difflib.SequenceMatcher(None, original, corrected)
    chunks = []
    
    for op, a_start, a_end, b_start, b_end in matcher.get_opcodes():
        a_text = original[a_start:a_end]
        b_text = corrected[b_start:b_end]
        
        if op == "equal":
            # 동일한 부분은 그대로
            chunks.append(a_text)
        elif op == "replace":
            # 교체: 원본 삭제 + 교정안 추가
            chunks.append(f"[-{a_text}-]")
            chunks.append(f"[+{b_text}+]")
        elif op == "delete":
            # 삭제: 원본 삭제 표시
            chunks.append(f"[-{a_text}-]")
        elif op == "insert":
            # 추가: 교정안 추가 표시
            chunks.append(f"[+{b_text}+]")
    
    return "".join(chunks)

def word_level_diff(original: str, corrected: str) -> str:
    """
    단어 단위로 diff를 생성합니다.
    
    Args:
        original: 원본 텍스트
        corrected: 교정된 텍스트
        
    Returns:
        단어 단위 diff 문자열
    """
    if not corrected:
        return ""
    
    if original == corrected:
        return ""
    
    # 단어로 분리
    orig_words = original.split()
    corr_words = corrected.split()
    
    # 단어 단위 diff
    matcher = difflib.SequenceMatcher(None, orig_words, corr_words)
    chunks = []
    
    for op, a_start, a_end, b_start, b_end in matcher.get_opcodes():
        a_words = orig_words[a_start:a_end]
        b_words = corr_words[b_start:b_end]
        
        if op == "equal":
            chunks.append(" ".join(a_words))
        elif op == "replace":
            chunks.append(f"[-{' '.join(a_words)}-]")
            chunks.append(f"[+{' '.join(b_words)}+]")
        elif op == "delete":
            chunks.append(f"[-{' '.join(a_words)}-]")
        elif op == "insert":
            chunks.append(f"[+{' '.join(b_words)}+]")
    
    return " ".join(chunks)

def highlight_changes(original: str, corrected: str, context_chars: int = 20) -> str:
    """
    변경된 부분을 강조하여 표시합니다.
    
    Args:
        original: 원본 텍스트
        corrected: 교정된 텍스트
        context_chars: 변경 부분 전후로 표시할 문자 수
        
    Returns:
        강조된 diff 문자열
    """
    if not corrected:
        return ""
    
    if original == corrected:
        return "변경 없음"
    
    matcher = difflib.SequenceMatcher(None, original, corrected)
    changes = []
    
    for op, a_start, a_end, b_start, b_end in matcher.get_opcodes():
        if op == "equal":
            continue
            
        # 변경 부분 전후 컨텍스트
        context_before = original[max(0, a_start - context_chars):a_start]
        context_after = original[a_end:min(len(original), a_end + context_chars)]
        
        if op == "replace":
            change = f"...{context_before}[-{original[a_start:a_end]}-]→[+{corrected[b_start:b_end]}+]{context_after}..."
        elif op == "delete":
            change = f"...{context_before}[-{original[a_start:a_end]}-]{context_after}..."
        elif op == "insert":
            change = f"...{context_before}[+{corrected[b_start:b_end]}+]{context_after}..."
        
        changes.append(change)
    
    return " | ".join(changes) if changes else "변경 없음"

def get_diff_statistics(original: str, corrected: str) -> dict:
    """
    diff 통계 정보를 반환합니다.
    
    Args:
        original: 원본 텍스트
        corrected: 교정된 텍스트
        
    Returns:
        통계 정보 딕셔너리
    """
    if not corrected:
        return {"error": "교정안이 없습니다"}
    
    if original == corrected:
        return {"changes": 0, "similarity": 1.0}
    
    matcher = difflib.SequenceMatcher(None, original, corrected)
    
    stats = {
        "changes": 0,
        "insertions": 0,
        "deletions": 0,
        "replacements": 0,
        "similarity": matcher.ratio()
    }
    
    for op, a_start, a_end, b_start, b_end in matcher.get_opcodes():
        if op == "equal":
            continue
        elif op == "replace":
            stats["replacements"] += 1
            stats["changes"] += 1
        elif op == "delete":
            stats["deletions"] += 1
            stats["changes"] += 1
        elif op == "insert":
            stats["insertions"] += 1
            stats["changes"] += 1
    
    return stats
