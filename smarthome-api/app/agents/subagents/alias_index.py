"""家庭级别的房间 / 设备别名倒排索引。

与 ``rule_engine`` 解耦：单独成文件后可以被其他模块（如
``context_engine`` / 未来的 NLU 工具）复用，而不必引入规则解析器。

.. note::
    任何对模块结构的改动请同步更新本文件顶部的 docstring 摘要。
"""

from __future__ import annotations

from collections.abc import Callable, Iterable


class AliasIndex:
    """家庭级别的房间 / 设备别名倒排索引。

    关键不变量：

    - 每次 ``set_*`` 后立即在内存中生效（热加载），与 ``funnel_alias_hot_reload``
      配合使用——关闭热加载时仍可工作，只是无法在线刷新。
    - 同一房间 / 设备的别名不会跨家庭污染（构造时绑定 ``household_id``）。
    - 冲突（同一别名映射到多个房间）时 ``resolve`` 返回空字符串，由上层追问。
    - **语义回退**：倒排未命中且未冲突时，可选地调用 ``embedding_resolver``；
      返回 ``None`` 或返回空串都视为「语义召回无果」，由调用方决定是否追问。
    """

    __slots__ = (
        "_conflicts",
        "_device_aliases",
        "_embedding_resolver",
        "_household_id",
        "_room_aliases",
        "version",
    )

    def __init__(
        self,
        household_id: int,
        *,
        embedding_resolver: Callable[[str, str], str | None] | None = None,
    ):
        """构造别名索引。

        ``embedding_resolver`` 形如 ``(kind, query) -> canonical | None``，
        ``kind`` 取 ``"room"`` 或 ``"device"``。未命中时返回 ``None``，命中时返回
        标准名（必须出现在已注册的 ``canonical_to_aliases`` 中，由调用方负责校验）。
        本索引不直接持有模型；上层（典型为 ``get_embedder()``）按需懒加载。
        """
        self._household_id = household_id
        # alias_lower -> canonical_name（房间）
        self._room_aliases: dict[str, str] = {}
        # alias_lower -> canonical_name（设备）
        self._device_aliases: dict[str, str] = {}
        # 同一 alias 多次 set 时记录，避免冲突被静默覆盖
        self._conflicts: set[str] = set()
        # 热加载协议：``set_*`` 会自增；``RuleEngine`` 据此决定是否换新
        self.version: int = 0
        self._embedding_resolver = embedding_resolver

    @property
    def household_id(self) -> int:
        return self._household_id

    def set_room_aliases(self, canonical_to_aliases: dict[str, Iterable[str]]) -> None:
        changed = False
        for canonical, aliases in canonical_to_aliases.items():
            for alias in aliases:
                key = alias.strip().lower()
                if not key:
                    continue
                if key in self._room_aliases and self._room_aliases[key] != canonical:
                    self._conflicts.add(key)
                if self._room_aliases.get(key) != canonical:
                    changed = True
                self._room_aliases[key] = canonical
        if changed:
            self.version += 1

    def set_device_aliases(
        self, canonical_to_aliases: dict[str, Iterable[str]]
    ) -> None:
        changed = False
        for canonical, aliases in canonical_to_aliases.items():
            for alias in aliases:
                key = alias.strip().lower()
                if not key:
                    continue
                if (
                    key in self._device_aliases
                    and self._device_aliases[key] != canonical
                ):
                    self._conflicts.add(key)
                if self._device_aliases.get(key) != canonical:
                    changed = True
                self._device_aliases[key] = canonical
        if changed:
            self.version += 1

    def resolve_room(self, alias: str) -> str:
        """按别名查找标准房间名。

        顺序：冲突检测 → 倒排索引 → 语义回退。冲突永不降级到语义层。
        """
        key = alias.strip().lower()
        if not key:
            return ""
        if key in self._conflicts:
            return ""
        direct = self._room_aliases.get(key)
        if direct:
            return direct
        return self._semantic_resolve("room", alias) or ""

    def resolve_device(self, alias: str) -> str:
        """按别名查找标准设备名，顺序同 :meth:`resolve_room`。"""
        key = alias.strip().lower()
        if not key:
            return ""
        if key in self._conflicts:
            return ""
        direct = self._device_aliases.get(key)
        if direct:
            return direct
        return self._semantic_resolve("device", alias) or ""

    def has_conflict(self, alias: str) -> bool:
        return alias.strip().lower() in self._conflicts

    def _semantic_resolve(self, kind: str, alias: str) -> str | None:
        """调用外部 ``embedding_resolver``；任何异常吞掉并返回 ``None``。

        这里不引入 ``try/except`` 之外的任何限流——上层负责将解析请求
        控制在合理频率（``RuleEngine.parse`` 入口已经做了预算检查）。
        """
        if self._embedding_resolver is None:
            return None
        try:
            return self._embedding_resolver(kind, alias)
        except Exception:  # noqa: BLE001
            # 语义召回失败不得影响主流程，倒排结果是兜底。
            return None
