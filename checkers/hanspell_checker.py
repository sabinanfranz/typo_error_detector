# -*- coding: utf-8 -*-
import time
import json
import os
from typing import Dict, Optional
from .base import BaseChecker

class HanspellChecker(BaseChecker):
    """Hanspell API 기반 맞춤법 검사기."""
    name = "hanspell"
    
    def __init__(self, rate_limit_per_sec: int = 5, cache_file: str = "hanspell_cache.json"):
        self.min_interval = 1.0 / max(rate_limit_per_sec, 1)
        self._last_request = 0.0
        self.cache_file = cache_file
        self.cache = self._JsonCache(cache_file)
        
        # hanspell 모듈 import 시도
        try:
            from hanspell import spell_checker
            self.spell_checker = spell_checker
            self._available = True
        except ImportError:
            print("경고: hanspell 모듈을 찾을 수 없습니다. pip install git+https://github.com/ssut/py-hanspell.git")
            self._available = False
    
    def check(self, sentence: str) -> Dict:
        """문장을 검사하여 맞춤법 오류를 찾습니다."""
        if not self._available:
            return {"flag": False, "meta": {"error": "hanspell 모듈 없음"}}
        
        # 캐시 확인
        cached = self.cache.get(sentence)
        if cached is not None:
            return cached
        
        # 레이트 리미팅
        self._rate_limit()
        
        try:
            result = self.spell_checker.check(sentence)
            
            # 결과 파싱 (버전별 호환성)
            if hasattr(result, 'checked'):
                corrected = result.checked
            elif hasattr(result, 'result'):
                corrected = result.result
            else:
                corrected = str(result)
            
            # 원문과 교정문 비교
            flag = corrected != sentence
            
            response = {
                "flag": flag,
                "suggestion": corrected if flag else None,
                "meta": {
                    "original": sentence,
                    "corrected": corrected,
                    "timestamp": time.time()
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
    
    def _rate_limit(self):
        """API 호출 속도 제한."""
        now = time.time()
        wait_time = self.min_interval - (now - self._last_request)
        if wait_time > 0:
            time.sleep(wait_time)
        self._last_request = time.time()
    
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
