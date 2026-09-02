from __future__ import annotations

import logging
import math
import threading
from collections.abc import Sequence

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingUnavailable:
    """依赖缺失或被关闭时返回的占位单例。

    所有方法都返回 ``None`` / ``False``，让上层把它当作"没有向量召回能力"。
    """

    __slots__ = ("reason",)

    def __init__(self, reason: str) -> None:
        self.reason = reason

    def encode(self, texts: Sequence[str]) -> list[list[float]] | None:
        return None

    @property
    def available(self) -> bool:
        return False


class SemanticEmbedder:
    """``sentence-transformers`` 模型的进程级单例。

    仅当 ``funnel_semantic_enabled=True`` 且依赖可用时才会真正持有模型。
    """

    __slots__ = ("_lock", "_max_seq_length", "_model")

    def __init__(self, model, max_seq_length: int) -> None:
        self._model = model
        self._max_seq_length = max_seq_length
        # 这里加锁避免并发请求互相覆盖 batch。
        self._lock = threading.Lock()

    @property
    def available(self) -> bool:
        return True

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        with self._lock:
            vectors = self._model.encode(
                list(texts),
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
                batch_size=8,
            )
        return vectors.tolist()


def _build_embedder() -> SemanticEmbedder | EmbeddingUnavailable:
    settings = get_settings()
    if not settings.funnel_semantic_enabled:
        return EmbeddingUnavailable("funnel_semantic_enabled=False")

    from sentence_transformers import SentenceTransformer

    try:
        model = SentenceTransformer(settings.funnel_semantic_model_path)
    except Exception as exc:  # noqa: BLE001
        # 模型加载失败（路径不存在 / 损坏 / OOM）：同样降级
        logger.warning("语义向量模型加载失败，降级为不可用：%s", exc)
        return EmbeddingUnavailable(f"model load failed: {exc}")

    max_len = settings.funnel_semantic_max_seq_length
    try:
        model.max_seq_length = max_len
    except Exception:  # noqa: BLE001, S110
        pass
    logger.info(
        "语义向量模型已加载：path=%s max_seq_length=%s",
        settings.funnel_semantic_model_path,
        max_len,
    )
    return SemanticEmbedder(model, max_len)


_embedder: SemanticEmbedder | EmbeddingUnavailable | None = None
_embedder_lock = threading.Lock()


def get_embedder() -> SemanticEmbedder | EmbeddingUnavailable:
    """获取进程级单例 embedder，首次调用时按需构建。"""
    global _embedder
    if _embedder is not None:
        return _embedder
    with _embedder_lock:
        if _embedder is None:
            _embedder = _build_embedder()
    return _embedder


def reset_embedder() -> None:
    """清空单例（测试 / 配置变更后使用）。"""
    global _embedder
    with _embedder_lock:
        _embedder = None


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """两个向量的余弦相似度；维度不一致或零向量时返回 0.0。

    与 ``SemanticEmbedder.encode(normalize_embeddings=True)`` 配合时，
    本函数退化为点积，避免重复 ``sqrt``。
    """
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for x, y in zip(a, b):
        dot += x * y
        norm_a += x * x
        norm_b += y * y
    if norm_a <= 0.0 or norm_b <= 0.0:
        return 0.0
    return dot / math.sqrt(norm_a * norm_b)
