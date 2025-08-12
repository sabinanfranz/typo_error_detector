# -*- coding: utf-8 -*-
from typing import Dict

class BaseChecker:
    """검사기 베이스 클래스."""
    name = "base"

    def check(self, sentence: str) -> Dict:
        """
        반환 형태:
        {
          "flag": bool,
          "suggestion": Optional[str] or "suggestions": list,
          "meta": Optional[dict]
        }
        """
        return {"flag": False}

    def shutdown(self):
        """필요 시 리소스 정리."""
        pass
