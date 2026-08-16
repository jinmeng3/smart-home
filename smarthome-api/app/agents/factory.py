import logging
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from threading import RLock

from app.agents.crypto import decrypt_api_key
from app.agents.errors import (
    ModelCredentialsMissing,
    ModelToolCallingUnsupported,
    UnsupportedModelProvider,
)
from app.core.config import Settings, get_settings
from app.models.ai import AIModel
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelAdapter:
    provider: str
    supports_tool_calls: bool = True
    builder: Callable[[AIModel], BaseChatModel] | None = None


class ModelFactory:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._adapters: dict[str, ModelAdapter] = {}
        self._register_defaults()

    def _register_defaults(self):
        for provider in ("openai", "deepseek"):
            self.register(
                ModelAdapter(
                    provider=provider,
                    builder=lambda cfg: ChatOpenAI(
                        model=cfg.name,
                        api_key=(decrypt_api_key(cfg.api_key) or "").strip(),
                        base_url=(cfg.api_endpoint or "").strip(),
                        temperature=cfg.temperature,
                        max_tokens=cfg.max_tokens,
                        timeout=self._settings.model_timeout_seconds,
                        max_retries=self._settings.model_max_retries,
                        stream_usage=True,
                    ),
                )
            )

    def register(self, adapter: ModelAdapter):
        self._adapters[adapter.provider.lower()] = adapter

    def build(self, config: AIModel) -> BaseChatModel:
        provider = (config.provider or "").strip().lower()
        if provider not in self._settings.supported_ai_providers:
            raise UnsupportedModelProvider(f"不支持模型提供商: {provider}")
        adapter = self._adapters.get(provider)
        if (
            adapter is None
            or not adapter.supports_tool_calls
            or adapter.builder is None
        ):
            raise ModelToolCallingUnsupported(
                f"提供商 '{provider}' 尚未适配 agent 工具调用, 请先接入验证"
            )

        api_key = decrypt_api_key(config.api_key) or ""
        if not api_key.strip():
            raise ModelCredentialsMissing("API key 缺失")

        api_endpoint = (config.api_endpoint or "").strip()
        if not api_endpoint:
            raise ModelCredentialsMissing("Base URL is missing")

        return adapter.builder(config)


class ModelCache:
    def __init__(self, max_cache_size: int, settings: Settings | None = None):
        self._settings = settings or get_settings()
        self._maxsize = max_cache_size
        self._items: OrderedDict[tuple[int, str], BaseChatModel] = OrderedDict()
        self._factory = ModelFactory(self._settings)
        self._lock = RLock()

    def get(self, config: AIModel) -> BaseChatModel:
        key = (config.id, config.updated_at.isoformat() if config.updated_at else "")
        with self._lock:
            cached = self._items.get(key)
            if cached is not None:
                self._items.move_to_end(key)
                return cached

            # 配置更新后立即移除旧实例，避免旧密钥长期留在内存中。
            stale_keys = [item_key for item_key in self._items if item_key[0] == config.id]
            for stale_key in stale_keys:
                self._items.pop(stale_key, None)

            model = self._factory.build(config)
            self._items[key] = model
            while len(self._items) > self._maxsize:
                self._items.popitem(last=False)
            return model