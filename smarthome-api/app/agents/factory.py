import logging
from collections import OrderedDict
from threading import RLock

from langchain_core.language_models import BaseChatModel

from app.agents.crypto import decrypt_api_key
from app.agents.errors import (
    ModelCredentialsMissing,
    ModelProtocolMismatch,
    UnsupportedModelProvider,
)
from app.agents.providers import OpenAICompatibleProvider, Provider
from app.core.config import Settings, get_settings
from app.models.ai import AIModel

logger = logging.getLogger(__name__)


class ModelsRegistry:
    """Models 容器（前台）——按 `provider` + `api` 双条件路由到对应 Provider。

    职责（对应 zod-ai 的 Models）：
    1. 注册各家 Provider（门店）；
    2. resolve(cfg)：按 provider 命中门店，并校验 api 协议在该 Provider 支持范围内；
    3. apply_auth(cfg)：解密 API key、校验凭证、合并附加请求头（来自 parameters.headers）；
    4. build(cfg)：把解析好的 client 参数注入 Provider.build()，返回 langchain 模型。
    """

    def __init__(self, settings: Settings):
        self._settings = settings
        self._providers: dict[str, Provider] = {}
        self._register_defaults()

    def _register_defaults(self):

        for provider_id in self._settings.supported_ai_providers:
            self.register(
                OpenAICompatibleProvider(
                    provider_id,
                    self._settings,
                )
            )

    def register(self, provider: Provider) -> None:
        self._providers[provider.id.lower()] = provider

    def resolve(self, cfg: AIModel) -> Provider:
        provider = self._providers.get((cfg.provider or "").strip().lower())
        if provider is None:
            raise UnsupportedModelProvider(f"不支持模型提供商: {cfg.provider}")
        api = (cfg.api or "openai-completions").strip().lower()
        if api not in provider.supported_api:
            raise ModelProtocolMismatch(
                f"{cfg.provider} 不支持协议 {api}（支持: {', '.join(provider.supported_api)}）"
            )
        return provider

    def apply_auth(self, cfg: AIModel) -> dict:
        """解析认证 + 合并 headers → 返回注入 Provider.build 的 client 参数。"""
        api_key = decrypt_api_key(cfg.api_key) or ""
        if not api_key.strip():
            raise ModelCredentialsMissing("API key 缺失")

        api_endpoint = (cfg.api_endpoint or "").strip()
        if not api_endpoint:
            raise ModelCredentialsMissing("Base URL is missing")

        headers = {}
        params = cfg.parameters or {}
        if isinstance(params.get("headers"), dict):
            headers = dict(params["headers"])

        return {
            "api_key": api_key,
            "base_url": api_endpoint,
            "headers": headers,
        }

    def build(self, cfg: AIModel) -> BaseChatModel:
        provider = self.resolve(cfg)
        client = self.apply_auth(cfg)
        return provider.build(cfg, client)


class ModelCache:
    def __init__(self, max_cache_size: int, settings: Settings | None = None):
        self._settings = settings or get_settings()
        self._maxsize = max_cache_size
        self._items: OrderedDict[tuple[int, str], BaseChatModel] = OrderedDict()
        self._registry = ModelsRegistry(self._settings)
        self._lock = RLock()

    def get(self, config: AIModel) -> BaseChatModel:
        key = (config.id, config.updated_at.isoformat() if config.updated_at else "")
        with self._lock:
            cached = self._items.get(key)
            if cached is not None:
                self._items.move_to_end(key)
                return cached

            stale_keys = [
                item_key for item_key in self._items if item_key[0] == config.id
            ]
            for stale_key in stale_keys:
                self._items.pop(stale_key, None)

            model = self._registry.build(config)
            self._items[key] = model
            while len(self._items) > self._maxsize:
                self._items.popitem(last=False)
            return model
