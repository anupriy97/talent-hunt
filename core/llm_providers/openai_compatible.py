from __future__ import annotations
from typing import Dict, Any
import requests
import json
from .base import LLMProvider

SYSTEM_PROMPT = """You are an information extraction engine for resumes.
Return ONLY valid JSON that matches the provided JSON schema. Do not add extra keys.
Rules:
- Do not guess. If missing, use null, empty string, or empty array as appropriate.
- Always populate these objects even if values are empty: target_fit, summary, skills.
- For target_fit.investment_approaches use only: Fundamental, Systematic (or empty).
- For target_fit.geographic_markets use only: US, Europe, APAC (or empty).
- Prefer short evidence snippets from the resume text for critical fields.
- Keep lists de-duplicated.
"""

USER_PROMPT_TEMPLATE = """Extract a structured resume record from the text below.

You MUST output JSON that conforms to this schema (JSON Schema):
{schema}

Resume text:
\"\"\"{resume_text}\"\"\"
"""

class OpenAICompatibleProvider(LLMProvider):
    """
    Works with any endpoint that exposes an OpenAI-compatible /v1/chat/completions API.
    """
    def __init__(self, api_base: str, api_key: str, model: str, timeout_s: int = 90):
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_s = timeout_s

    def parse_resume(self, resume_id: str, resume_text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        user_prompt = USER_PROMPT_TEMPLATE.format(schema=json.dumps(schema), resume_text=resume_text[:120000])
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0,
            # Many compatible providers support some variant of JSON mode:
            "response_format": {"type": "json_object"},
        }
        r = requests.post(url, headers=headers, json=payload, timeout=self.timeout_s)
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        parsed["resume_id"] = resume_id  # ensure stable id
        return parsed
