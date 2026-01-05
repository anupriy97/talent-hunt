from __future__ import annotations
from typing import Dict, Any

class LLMProvider:
    def parse_resume(self, resume_id: str, resume_text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
