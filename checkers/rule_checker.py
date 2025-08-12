# -*- coding: utf-8 -*-
import re
import yaml
import os
from typing import Dict, List, Optional
from .base import BaseChecker

# 기본 규칙들
DEFAULT_RULES = [
    {
        "name": "되/돼",
        "pattern": r"(되(?=\s*요|[^가-힣]|$))|(?<!되|돼)돼(?!지)",
        "hint": "문맥에 맞는 되/돼 확인"
    },
    {
        "name": "안/않",
        "pattern": r"\b않(아|고|다|는)\b|\b안(되|돼)",
        "hint": "부정(안) vs 부정용언(않) 점검"
    },
    {
        "name": "'것 같다' 띄어쓰기",
        "pattern": r"것같",
        "hint": "'것 같다'로 띄어쓰기"
    },
    {
        "name": "수+단위 띄어쓰기",
        "pattern": r"(\d+)([가-힣]+)",
        "hint": "숫자와 단위 사이 띄어쓰기 확인"
    }
]

class RuleChecker(BaseChecker):
    """규칙 기반 오류 검사기."""
    name = "rule"
    
    def __init__(self, rules_yaml: Optional[str] = None, whitelist_path: Optional[str] = None):
        self.rules = self._load_rules(rules_yaml)
        self.whitelist = self._load_whitelist(whitelist_path)
    
    def check(self, sentence: str) -> Dict:
        """규칙에 따라 문장을 검사합니다."""
        # 화이트리스트 체크
        if any(term in sentence for term in self.whitelist):
            return {"flag": False}
        
        hits = []
        
        for rule in self.rules:
            try:
                if re.search(rule["pattern"], sentence):
                    hits.append({
                        "rule": rule["name"],
                        "hint": rule["hint"]
                    })
            except re.error as e:
                print(f"규칙 '{rule['name']}'의 정규식 오류: {e}")
                continue
        
        return {
            "flag": bool(hits),
            "suggestions": hits if hits else None,
            "meta": {"hits": hits}
        }
    
    def _load_rules(self, rules_yaml: Optional[str]) -> List[Dict]:
        """YAML 파일에서 규칙을 로드합니다."""
        if not rules_yaml or not os.path.exists(rules_yaml):
            return DEFAULT_RULES
        
        try:
            with open(rules_yaml, 'r', encoding='utf-8') as f:
                loaded_rules = yaml.safe_load(f)
                if loaded_rules and isinstance(loaded_rules, list):
                    return loaded_rules
        except Exception as e:
            print(f"규칙 파일 로드 실패: {e}")
        
        return DEFAULT_RULES
    
    def _load_whitelist(self, whitelist_path: Optional[str]) -> set:
        """화이트리스트 파일을 로드합니다."""
        whitelist = set()
        
        if not whitelist_path or not os.path.exists(whitelist_path):
            return whitelist
        
        try:
            with open(whitelist_path, 'r', encoding='utf-8') as f:
                for line in f:
                    term = line.strip()
                    if term and not term.startswith('#'):
                        whitelist.add(term)
        except Exception as e:
            print(f"화이트리스트 파일 로드 실패: {e}")
        
        return whitelist
    
    def add_rule(self, name: str, pattern: str, hint: str = ""):
        """새로운 규칙을 추가합니다."""
        self.rules.append({
            "name": name,
            "pattern": pattern,
            "hint": hint
        })
    
    def add_whitelist_term(self, term: str):
        """화이트리스트에 용어를 추가합니다."""
        self.whitelist.add(term)
