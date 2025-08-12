# -*- coding: utf-8 -*-
import json
import os
from typing import Dict, Optional
from .base import BaseChecker

class SpacingChecker(BaseChecker):
    """PyKoSpacing 기반 띄어쓰기 검사기."""
    name = "spacing"
    
    def __init__(self, cache_file: str = "spacing_cache.json"):
        self.cache_file = cache_file
        self.cache = self._JsonCache(cache_file)
        
        # pykospacing 모듈 import 시도
        try:
            from pykospacing import Spacing
            self.model = Spacing()
            self._available = True
        except ImportError:
            print("경고: pykospacing 모듈을 찾을 수 없습니다. pip install pykospacing")
            self._available = False
    
    def check(self, sentence: str) -> Dict:
        """문장의 띄어쓰기를 검사합니다."""
        if not self._available:
            return {"flag": False, "meta": {"error": "pykospacing 모듈 없음"}}
        
        # 캐시 확인
        cached = self.cache.get(sentence)
        if cached is not None:
            return cached
        
        try:
            # 띄어쓰기 교정
            corrected = self.model(sentence)
            
            # 의미있는 변경인지 확인
            flag = self._significant_change(sentence, corrected)
            
            response = {
                "flag": flag,
                "suggestion": corrected if flag else None,
                "meta": {
                    "original": sentence,
                    "corrected": corrected,
                    "original_length": len(sentence),
                    "corrected_length": len(corrected)
                }
            }
            
            # 캐시에 저장
            self.cache.set(sentence, response)
            
            return response
            
        except Exception as e:
            return {
                "flag": False,
                "meta": {"error": str(e)}
            }
    
    def _significant_change(self, original: str, corrected: str) -> bool:
        """띄어쓰기 변경이 의미있는지 판단."""
        if original == corrected:
            return False
        
        # 길이 차이가 1 이상이면 의미있는 변경
        if abs(len(corrected) - len(original)) >= 1:
            return True
        
        # 공백 개수 변화가 있으면 의미있는 변경
        orig_spaces = original.count(' ')
        corr_spaces = corrected.count(' ')
        if abs(corr_spaces - orig_spaces) >= 1:
            return True
        
        # 단어 수 변화가 있으면 의미있는 변경
        orig_words = len(original.split())
        corr_words = len(corrected.split())
        if abs(corr_words - orig_words) >= 1:
            return True
        
        return False
    
    def shutdown(self):
        """캐시를 파일에 저장."""
        self.cache.flush()
    
    class _JsonCache:
        """JSON 파일 기반 캐시."""
        
        def __init__(self, filename: str):
            self.filename = filename
            self.data = {}
            self._load()
        
        def _load(self):
            """캐시 파일 로드."""
            try:
                if os.path.exists(self.filename):
                    with open(self.filename, 'r', encoding='utf-8') as f:
                        self.data = json.load(f)
            except Exception:
                self.data = {}
        
        def get(self, key: str) -> Optional[Dict]:
            """캐시에서 값 조회."""
            return self.data.get(key)
        
        def set(self, key: str, value: Dict):
            """캐시에 값 저장."""
            self.data[key] = value
        
        def flush(self):
            """캐시를 파일에 저장."""
            try:
                with open(self.filename, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
