from __future__ import annotations

import os

from providers.openai_provider import OpenAIProvider


class OpenRouterProvider(OpenAIProvider):
    """VietAPI — OpenAI-compatible endpoint (replaces OpenRouter)."""

    def __init__(self) -> None:
        super().__init__(
            api_key_env="OPENROUTER_API_KEY",
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://api.vietapi.tech/v1"),
            default_model="deepseek-v4-flash",
        )
