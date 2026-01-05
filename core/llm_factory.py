from __future__ import annotations
from typing import Any
import os
from .llm_providers.mock import MockProvider
from .llm_providers.openai_compatible import OpenAICompatibleProvider

def get_provider():
    provider = os.getenv("LLM_PROVIDER", "mock").strip().lower()
    if provider == "mock":
        return MockProvider()
    if provider == "openai_compatible":
        api_base = os.environ["LLM_API_BASE"]
        api_key = os.environ["LLM_API_KEY"]
        model = os.environ["LLM_MODEL"]
        return OpenAICompatibleProvider(api_base=api_base, api_key=api_key, model=model)
    raise ValueError(f"Unknown LLM_PROVIDER={provider}. Use mock or openai_compatible.")
