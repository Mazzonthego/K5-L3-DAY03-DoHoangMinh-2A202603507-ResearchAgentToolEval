from __future__ import annotations

import os

from providers.openai_provider import OpenAIProvider


class VietAPIProvider(OpenAIProvider):
    """VietAPI - OpenAI-compatible Chat Completions surface."""

    def __init__(self) -> None:
        super().__init__(
            api_key_env="OPENROUTER_API_KEY",  # Reuse existing key from .env
            base_url=os.getenv("VIETAPI_BASE_URL", "https://api.vietapi.tech/v1"),
            default_model="nemetron-3-ultra",
        )