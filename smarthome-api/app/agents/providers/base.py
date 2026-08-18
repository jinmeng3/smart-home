from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.models.ai import AIModel
from langchain_core.language_models import BaseChatModel


@dataclass(frozen=True)
class ProviderAuth:
    """Provider 的认证方式描述：API key（加解密存储）或 OAuth。"""

    api_key: bool = True
    oauth: bool = False


class Provider(ABC):
    """Provider —— 一家 AI 服务商（对应 zod-ai 的 Provider）。

    负责：模型目录（get_models）、认证方式（auth）、把配置构建成可调用的
    langchain 模型（build）。由 ModelsRegistry（前台）按 provider + api 路由过来。
    """

    id: str
    name: str
    auth: ProviderAuth = field(default_factory=ProviderAuth)
    supported_api: tuple[str, ...] = ("openai-completions",)

    @abstractmethod
    def build(self, cfg: AIModel, client: dict) -> BaseChatModel:
        """根据模型配置和已解析的认证/头信息构建 langchain 模型。

        client 由 ModelsRegistry 注入：{api_key, base_url, headers, extra_body, ...}
        """

    def get_models(self) -> list[dict]:
        """当前已知的模型目录（可选覆盖）。"""
        return []
