from __future__ import annotations

from app.agents.providers.base import Provider, ProviderAuth
from app.core.config import Settings
from app.models.ai import AIModel
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI


class OpenAICompatibleProvider(Provider):
    id: str
    name: str
    auth: ProviderAuth
    supported_api: tuple[str, ...] = ("openai-completions", "openai-responses")

    def __init__(self, provider_id: str, settings: Settings):
        self.id = provider_id
        self.auth = ProviderAuth(api_key=True)
        self._settings = settings

    def build(self, cfg: AIModel, client: dict) -> BaseChatModel:
        extra_body: dict = dict(client.get("extra_body") or {})
        # 兼容配置里允许按协议透传自定义参数（如 thinking、reasoning_effort 等）
        if cfg.compat and isinstance(cfg.compat, dict):
            for key in (
                "thinking",
                "reasoning_effort",
                "enable_thinking",
                "max_completion_tokens",
            ):
                if key in cfg.compat:
                    extra_body[key] = cfg.compat[key]

        model_kwargs: dict = {
            "model": cfg.name,
            "api_key": client["api_key"],
            "base_url": client["base_url"],
            "temperature": cfg.temperature,
            "max_tokens": cfg.max_tokens,
            "timeout": self._settings.model_timeout_seconds,
            "max_retries": self._settings.model_max_retries,
            "stream_usage": True,
        }
        if client.get("headers"):
            model_kwargs["default_headers"] = client["headers"]
        if extra_body:
            model_kwargs["extra_body"] = extra_body

        return ChatOpenAI(**model_kwargs)
