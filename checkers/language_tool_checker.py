# -*- coding: utf-8 -*-
from typing import Dict
from .base import BaseChecker

class LanguageToolChecker(BaseChecker):
    """LanguageTool 기반 맞춤법/문법 검사기."""
    name = "languagetool"

    def __init__(self):
        try:
            import language_tool_python  # type: ignore
            self.tool = language_tool_python.LanguageTool('ko')
            self._available = True
        except Exception as e:
            print(f"경고: LanguageTool 초기화 실패: {e}")
            self._available = False
            self.tool = None

    def check(self, sentence: str) -> Dict:
        if not self._available or self.tool is None:
            return {"flag": False, "meta": {"error": "languagetool 모듈 없음"}}

        matches = self.tool.check(sentence)
        if not matches:
            return {"flag": False}

        suggestions = []
        for m in matches:
            if m.replacements:
                suggestions.append(m.replacements[0])
        return {
            "flag": True,
            "suggestions": suggestions,
            "meta": {"match_count": len(matches)}
        }

    def shutdown(self):
        try:
            if self.tool:
                self.tool.close()
        except Exception:
            pass
