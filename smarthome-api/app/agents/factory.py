import logging
from collections import OrderedDict

from app.agents.errors import (
    ModelCredentialsMissing,
    UnsupportedModelProvider,
)
from app.core.config import Settings, get_settings
from app.models.ai import AIModel
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


def create_chat_model(
    config: AIModel, settings: Settings | None = None
) -> BaseChatModel:
    settings = settings or get_settings()
    provider = config.provider.strip().lower()
    if provider not in settings.supported_ai_providers:
        raise UnsupportedModelProvider(f"Unsupported AI provider: {provider}")

    api_key = (config.api_key or "").strip()
    if not api_key:
        raise ModelCredentialsMissing("API key is missing")

    api_endpoint = (config.api_endpoint or "").strip()
    if not api_endpoint:
        raise ModelCredentialsMissing("Base URL is missing")
    # 只适配OpenAI兼容接口
    model = ChatOpenAI(model=config.name, api_key=api_key, base_url=api_endpoint)

    return model


class ModelCache:
    def __init__(self, max_cache_size: int):
        self._maxsize = max_cache_size
        self._items: OrderedDict[tuple[int, str], BaseChatModel] = OrderedDict()

    def get(self, config: AIModel, settings: Settings | None = None) -> BaseChatModel:
        key = (config.id, config.updated_at.isoformat() if config.updated_at else "")
        cached = self._items.get(key)
        if cached is not None:
            return cached  # 没有修改则返回之前使用的模型
        # 修改则创建新模型并缓存
        model = create_chat_model(config, settings)
        self._items[key] = model
        self._items.move_to_end(key)
        while len(self._items) > self._maxsize:
            self._items.popitem(last=False)
        return model
