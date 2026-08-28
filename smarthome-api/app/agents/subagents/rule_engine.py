from __future__ import annotations

import re
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any

from app.agents.subagents.router import DOMAIN_KEYWORDS
from app.core.config import get_settings

# ---------------------------------------------------------------------------
# 数据契约
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class WriteProposal:
    """规则层直接产出的可执行写提案。

    结构与 ``WRITE_TOOL_NAMES`` 中写工具的参数一致，可直接交给
    ``risk_check`` → ``approval`` 链路。
    """

    tool: str
    args: dict[str, Any]


@dataclass(frozen=True, slots=True)
class RuleParseResult:
    """规则层解析结果。

    Attributes:
        matched: 是否成功解析为可执行意图。
        intent: 意图类别（``control`` / ``scene`` / ``query`` / ``schedule`` /
            ``clarify``），未匹配时为空字符串。
        domain: 命中的领域标签，与 ``DOMAIN_KEYWORDS`` 的 key 对齐。
        confidence: 匹配置信度，区间 [0, 1]，< ``funnel_rule_confidence_low``
            视为不可用。
        action: 动作枚举（``on`` / ``off`` / ``set_temperature`` /
            ``set_position`` / ``trigger`` / ``query_state`` / ``schedule``）。
        entity: 目标实体类型（``light`` / ``air_conditioner`` / ``curtain`` /
            ``socket`` / ``device`` / ``scene``），未识别时为空字符串。
        entity_ref: 解析出的实体引用文本（房间名 + 设备名 / 别名），用于在
            上下文中反查真实设备。
        params: 提取出的参数（如 ``{"temperature": 26}``）。
        response_text: 直接返回给用户的自然语言答案（用于「现在几点了」等
            简单查询场景）。
        write_proposals: 规则层直出的写提案列表；调用方仍需经 ``risk_check``
            审批。
        needs_clarification: 是否需要追问用户（命中 0.8 ~ 0.95 的模糊区间时
            设为 True）。
        clarification_prompt: 追问时建议使用的提示文本。
        elapsed_ms: 实际解析耗时（毫秒），用于性能监控。
    """

    matched: bool
    intent: str = ""
    domain: str = ""
    confidence: float = 0.0
    action: str = ""
    entity: str = ""
    entity_ref: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    response_text: str = ""
    write_proposals: tuple[WriteProposal, ...] = ()
    needs_clarification: bool = False
    clarification_prompt: str = ""
    elapsed_ms: int = 0


# ---------------------------------------------------------------------------
# 词典
# ---------------------------------------------------------------------------


# 中文停用词：出现在实体前的修饰词，匹配时需要忽略。
_ROOM_NOISE = ("的", "的", "里", "里面", "中", "内", "上")

# 房间 → 设备类型 的语义提示：当用户说「客厅灯」时，entity 优先取 light。
_ROOM_DEVICE_HINTS: dict[str, str] = {
    "灯": "light",
    "灯光": "light",
    "吊灯": "light",
    "台灯": "light",
    "筒灯": "light",
    "空调": "air_conditioner",
    "冷气": "air_conditioner",
    "暖气": "air_conditioner",
    "窗帘": "curtain",
    "帘子": "curtain",
    "插座": "socket",
    "排插": "socket",
    "电视": "socket",  # 常用插座供电
    "扫地": "socket",  # 扫地机器人常以插座控制电源
    "机器人": "socket",
}

# 动作 → 设备类型 兼容表：未识别设备类型时回退为通用 device。
_ACTION_DEFAULT_ENTITY = {
    "on": "device",
    "off": "device",
    "set_temperature": "air_conditioner",
    "set_position": "curtain",
}

# 「打开 / 关闭」类动作的中文触发词 → 内部动作枚举。
_TURN_ON_PATTERNS = (
    "打开",
    "开",
    "启动",
    "开启",
    "亮一下",
    "亮起来",
    "开一下",
    "帮我开",
)
_TURN_OFF_PATTERNS = ("关闭", "关", "关上", "关掉", "熄", "关一下", "帮我关")

# 「设置」类动作的触发词。
_SET_TEMP_PATTERNS = (
    "调到",
    "设置成",
    "设为",
    "设置到",
    "调到",
    "调成",
    "调至",
    "设定",
)
_SET_POSITION_PATTERNS = ("开到", "关到", "调到", "设置到", "开合", "拉到")

# 「查询」类动作的触发词。
_QUERY_STATE_PATTERNS = (
    "现在",
    "多少",
    "几度",
    "怎么样",
    "如何",
    "状态",
    "开没开",
    "开着没",
)

# 预设场景关键词 → 触发场景执行。
_SCENE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "home": ("我回来了", "回来了", "回家", "到家了"),
    "leave": ("我出门了", "出门了", "离家", "走了", "外出了"),
    "sleep": ("睡觉了", "我要睡了", "晚安", "去睡"),
    "wake": ("起床了", "早安", "起来了", "醒来了"),
    "movie": ("观影模式", "看电影", "开始观影", "电影模式"),
    "reading": ("阅读模式", "我要看书", "开始阅读"),
    "cooking": ("做饭了", "烹饪模式", "开始做饭"),
}


# ---------------------------------------------------------------------------
# 预编译正则
# ---------------------------------------------------------------------------


_NUMBER_RE = re.compile(r"(-?\d+(?:\.\d+)?)")
_TEMP_RE = re.compile(r"(-?\d+(?:\.\d+)?)\s*(?:度|℃|°C|°|C)(?!\w)", re.IGNORECASE)
_PERCENT_RE = re.compile(r"(-?\d+(?:\.\d+)?)\s*(?:%|百分之|成)(?!\w)")
_TURN_ON_RE = re.compile("|".join(_TURN_ON_PATTERNS))
_TURN_OFF_RE = re.compile("|".join(_TURN_OFF_PATTERNS))
_SET_TEMP_RE = re.compile("|".join(_SET_TEMP_PATTERNS))
_SET_POS_RE = re.compile("|".join(_SET_POSITION_PATTERNS))
_QUERY_RE = re.compile("|".join(_QUERY_STATE_PATTERNS))
_ROOM_NOISE_RE = re.compile("(" + "|".join(re.escape(w) for w in _ROOM_NOISE) + ")")


# ---------------------------------------------------------------------------
# 别名倒排索引
# ---------------------------------------------------------------------------


class AliasIndex:
    """家庭级别的房间 / 设备别名倒排索引。

    关键不变量：

    - 每次 ``set_*`` 后立即在内存中生效（热加载），与 ``funnel_alias_hot_reload``
      配合使用——关闭热加载时仍可工作，只是无法在线刷新。
    - 同一房间 / 设备的别名不会跨家庭污染（构造时绑定 ``household_id``）。
    - 冲突（同一别名映射到多个房间）时 ``resolve`` 返回空字符串，由上层追问。
    """

    __slots__ = (
        "_conflicts",
        "_device_aliases",
        "_household_id",
        "_room_aliases",
        "version",
    )

    def __init__(self, household_id: int):
        self._household_id = household_id
        # alias_lower -> canonical_name（房间）
        self._room_aliases: dict[str, str] = {}
        # alias_lower -> canonical_name（设备）
        self._device_aliases: dict[str, str] = {}
        # 同一 alias 多次 set 时记录，避免冲突被静默覆盖
        self._conflicts: set[str] = set()
        # 热加载协议：``set_*`` 会自增；``RuleEngine`` 据此决定是否换新
        self.version: int = 0

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
        """按别名查找标准房间名；冲突或未命中时返回空字符串。"""
        key = alias.strip().lower()
        if key in self._conflicts:
            return ""
        return self._room_aliases.get(key, "")

    def resolve_device(self, alias: str) -> str:
        """按别名查找标准设备名；冲突或未命中时返回空字符串。"""
        key = alias.strip().lower()
        if key in self._conflicts:
            return ""
        return self._device_aliases.get(key, "")

    def has_conflict(self, alias: str) -> bool:
        return alias.strip().lower() in self._conflicts


# ---------------------------------------------------------------------------
# 规则引擎
# ---------------------------------------------------------------------------


class RuleEngine:
    """规则层意图解析器。

    使用方式：

    .. code-block:: python

        engine = RuleEngine(alias_index=AliasIndex(household_id=1))
        result = engine.parse("打开客厅灯")
        if result.matched and result.confidence >= 0.95:
            for proposal in result.write_proposals:
                # 交给 risk_check → approval
                ...
    """

    # 置信度档位：精确匹配 / 模糊匹配 / 拒识。
    _CONF_HIGH = 0.97
    _CONF_MID = 0.85
    _CONF_LOW = 0.4

    def __init__(
        self,
        *,
        alias_index: AliasIndex | None = None,
        alias_provider: Callable[[], AliasIndex | None] | None = None,
    ):
        # 静态别名索引：调用方在构造时绑定，后续不更新。
        self._alias_index = alias_index
        # 动态别名供应者：每次 ``parse`` 检查 ``version``，变化时换新。
        # 与 ``funnel_alias_hot_reload`` 配合使用——开启热加载时上层
        # 传一个返回当前 ``AliasIndex`` 的 callable（通常从设备 / 房间表
        # 重建），关闭时保持一次性绑定。
        self._alias_provider = alias_provider
        # 已持有的 provider 索引 ``version``，避免重复 setattr
        self._provider_version: int | None = None

    def _refresh_alias_index(self) -> None:
        """调用 ``alias_provider`` 检查 ``version``；变化则换新 ``_alias_index``。

        关闭热加载（``funnel_alias_hot_reload=False``）时直接返回，保持
        一次性绑定的现有行为。
        """
        if self._alias_provider is None:
            return
        if not get_settings().funnel_alias_hot_reload:
            return
        current = self._alias_provider()
        if current is None:
            return
        if self._provider_version is None:
            # 首次调用：直接绑定并记录 version
            self._alias_index = current
            self._provider_version = current.version
            return
        if current.version != self._provider_version:
            self._alias_index = current
            self._provider_version = current.version

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

    def parse(self, message: str) -> RuleParseResult:
        """同步解析；任何异常被吞掉并返回 ``matched=False``。

        性能预算：函数入口用 ``time.perf_counter`` 计时，超出
        ``funnel_rule_max_duration_ms`` 时立刻返回空匹配，由路由器把请求
        抛给上层。
        """
        settings = get_settings()
        self._started_at = time.perf_counter()
        budget_ms = settings.funnel_rule_max_duration_ms
        # 入口先做别名热加载检查（与解析路径解耦）
        self._refresh_alias_index()
        text = (message or "").strip()
        if not text:
            return RuleParseResult(matched=False, elapsed_ms=self._elapsed_ms())

        # 0. 复合意图检测：含连接词 / 决策词 / 跨域信号时，规则层不能拍板，
        #    一律由兑底层处理。避免「我睡觉了，顺便看看明天天气决定要不要开加湿器」
        #    被误识别为「睡觉了」场景。
        if self._is_composite_intent(text):
            return RuleParseResult(
                matched=False, intent="composite", domain="", confidence=0.0,
                elapsed_ms=self._elapsed_ms(),
            )

        # 1. 简单查询（最廉价）
        if self._over_budget(budget_ms):
            return RuleParseResult(matched=False, elapsed_ms=self._elapsed_ms())
        query_result = self._try_query(text)
        if query_result is not None:
            return query_result

        # 2. 固定场景
        if self._over_budget(budget_ms):
            return RuleParseResult(matched=False, elapsed_ms=self._elapsed_ms())
        scene_result = self._try_scene(text)
        if scene_result is not None:
            return scene_result

        # 3. 快捷自动化（带时间的「十分钟后关电视」类）
        if self._over_budget(budget_ms):
            return RuleParseResult(matched=False, elapsed_ms=self._elapsed_ms())
        schedule_result = self._try_schedule(text)
        if schedule_result is not None:
            return schedule_result

        # 4. 直接控制（开 / 关 / 调温 / 调开合）
        if self._over_budget(budget_ms):
            return RuleParseResult(matched=False, elapsed_ms=self._elapsed_ms())
        control_result = self._try_control(text)
        if control_result is not None:
            return control_result

        # 5. 都没命中 → 拒识
        return RuleParseResult(
            matched=False, intent="", domain="", confidence=0.0, elapsed_ms=self._elapsed_ms()
        )

    def _is_composite_intent(self, text: str) -> bool:
        """检测「复合 / 跨域 / 决策型」意图，命中则让规则层拒识。

        信号：并列连接词（「顺便」「还有」「另外」）、决策词（「决定要不要
        」「看看」）、跨域多动作（同时含控制词 + 查询 / 场景词）。
        """
        if not text:
            return False
        composite_signals = ("顺便", "还有", "另外", "同时", "再帮我", "然后")
        decision_signals = ("决定", "要不要", "看看", "需不需要", "是不是要")
        for signal in (*composite_signals, *decision_signals):
            if signal in text:
                return True
        return False

    # ------------------------------------------------------------------
    # 子解析器
    # ------------------------------------------------------------------

    def _try_query(self, text: str) -> RuleParseResult | None:
        if not _QUERY_RE.search(text):
            return None

        # 命中「现在几点了」
        if re.search(r"几[点时](\d+)?|现在时间|当前时间", text):
            return RuleParseResult(
                matched=True,
                intent="query",
                domain="device",
                confidence=self._CONF_HIGH,
                action="query_state",
                entity="clock",
                response_text="",  # 由调用方填入当前时间
                elapsed_ms=self._elapsed_ms(),
            )

        # 命中「室内 / 房间 温度 多少」
        if re.search(r"温度|几度|多暖|多冷", text):
            return RuleParseResult(
                matched=True,
                intent="query",
                domain="comfort",
                confidence=self._CONF_HIGH,
                action="query_state",
                entity="temperature",
                entity_ref=self._extract_room(text),
                response_text="",
                elapsed_ms=self._elapsed_ms(),
            )

        # 命中「湿度」
        if re.search(r"湿度|干不干|潮不潮", text):
            return RuleParseResult(
                matched=True,
                intent="query",
                domain="comfort",
                confidence=self._CONF_HIGH,
                action="query_state",
                entity="humidity",
                entity_ref=self._extract_room(text),
                response_text="",
                elapsed_ms=self._elapsed_ms(),
            )

        return None

    def _try_scene(self, text: str) -> RuleParseResult | None:
        for scene_id, keywords in _SCENE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    return RuleParseResult(
                        matched=True,
                        intent="scene",
                        domain="scene",
                        confidence=self._CONF_HIGH,
                        action="trigger",
                        entity="scene",
                        entity_ref=scene_id,
                        write_proposals=(
                            WriteProposal(
                                tool="execute_scene",
                                args={"scene_id": scene_id},
                            ),
                        ),
                        elapsed_ms=self._elapsed_ms(),
                    )
        return None

    def _try_schedule(self, text: str) -> RuleParseResult | None:
        """检测「十分钟后关电视」类快捷自动化。

        此类在本层不直接执行（定时器依赖边缘网关），而是把可执行提案与
        ``schedule_at`` 透传给上层；上层可选择写入本地定时器或交给 LLM 走
        ``create_automation``。
        """
        # 支持阿拉伯数字（10）与中文数字（十）。需在本层通过 -- 以防回退。
        delay_match = re.search(
            r"(\d+|[一两二三四五六七八九十百千]+)\s*(分钟|秒钟|秒|小时|分)(?:之?后|再)|"
            r"等(\d+|[一两二三四五六七八九十百千]+)\s*(分钟|秒钟|秒|小时|分)",
            text,
        )
        if delay_match is None:
            return None
        raw_amount = delay_match.group(1) or delay_match.group(3)
        unit = delay_match.group(2) or delay_match.group(4)
        amount = _parse_chinese_number(raw_amount)
        multiplier = {"秒": 1, "秒钟": 1, "分钟": 60, "分": 60, "小时": 3600}.get(unit, 60)
        delay_seconds = amount * multiplier

        # 复用控制类解析得到基础动作
        base = self._try_control(text)
        if base is None or not base.write_proposals:
            return None
        enriched_params = dict(base.params)
        enriched_params["delay_seconds"] = delay_seconds
        # 把原始写提案的 args 注入 delay
        new_proposals = tuple(
            WriteProposal(tool=p.tool, args={**p.args, "delay_seconds": delay_seconds})
            for p in base.write_proposals
        )
        return RuleParseResult(
            matched=True,
            intent="schedule",
            domain=base.domain,
            confidence=self._CONF_MID,
            action=base.action,
            entity=base.entity,
            entity_ref=base.entity_ref,
            params=enriched_params,
            write_proposals=new_proposals,
            needs_clarification=True,
            clarification_prompt=(
                f"将在 {amount}{unit}后执行该操作，届时是否需要二次确认？"
            ),
            elapsed_ms=self._elapsed_ms(),
        )

    def _try_control(self, text: str) -> RuleParseResult | None:
        """直接控制：「打开客厅灯」「空调调到 26 度」「关闭窗帘」。"""
        action = self._detect_action(text)
        if action is None:
            return None
        entity, entity_ref, params = self._extract_entity(text, action)

        # 解析不到任何实体引用（如「打开」单字）→ 拒识，避免误触执行。
        if not entity_ref:
            return None

        # 解析到实体但别名为空（用户只说了「空调」）→ 给中等置信度
        confidence = self._CONF_HIGH if entity_ref else self._CONF_MID

        # 写提案：只生成「待解析」形态（不含 device_id），由路由器 / 执行器
        # 通过 ``entity_ref`` 在家庭设备表中反查后填充。
        proposals: list[WriteProposal] = []
        if action == "on":
            proposals.append(
                WriteProposal(
                    tool="set_device_power",
                    args={"power": "on"},
                )
            )
        elif action == "off":
            proposals.append(
                WriteProposal(
                    tool="set_device_power",
                    args={"power": "off"},
                )
            )
        elif action == "set_temperature":
            temp = params.get("temperature")
            if temp is None:
                return None
            proposals.append(
                WriteProposal(
                    tool="set_device_temperature",
                    args={"temperature": float(temp)},
                )
            )
        elif action == "set_position":
            position = params.get("position", 100 if "开" in text else 0)
            proposals.append(
                WriteProposal(
                    tool="set_curtain_position",
                    args={"position": int(position)},
                )
            )
        else:
            return None

        # 模糊匹配（0.8 ~ 0.95）→ 触发追问
        needs_clarification = confidence < self._CONF_HIGH

        return RuleParseResult(
            matched=True,
            intent="control",
            domain=self._domain_of_entity(entity),
            confidence=confidence,
            action=action,
            entity=entity,
            entity_ref=entity_ref,
            params=params,
            write_proposals=tuple(proposals),
            needs_clarification=needs_clarification,
            clarification_prompt=(
                f"请确认要操作的目标是「{entity_ref or entity}」吗？"
                if needs_clarification
                else ""
            ),
            elapsed_ms=self._elapsed_ms(),
        )

    # ------------------------------------------------------------------
    # 辅助
    # ------------------------------------------------------------------

    def _detect_action(self, text: str) -> str | None:
        # 顺序：先识别「调温 / 调位置」这类带数值的设置动作，避免被
        # 「开」这种单字动作误判。
        if _SET_TEMP_RE.search(text) and _TEMP_RE.search(text):
            return "set_temperature"
        if _SET_POS_RE.search(text) and _PERCENT_RE.search(text):
            return "set_position"
        if _TURN_OFF_RE.search(text):
            return "off"
        if _TURN_ON_RE.search(text):
            return "on"
        return None

    def _extract_entity(
        self, text: str, action: str
    ) -> tuple[str, str, dict[str, Any]]:
        """从原始文本里抽取 (entity, entity_ref, params)。

        - entity：设备类型枚举；
        - entity_ref：实体引用文本（房间名 + 设备 / 别名），用于上层反查真实设备；
        - params：动作参数（温度 / 百分比等）。
        """
        params: dict[str, Any] = {}

        # 1. 优先识别显式的设备类型关键词
        entity = ""
        matched_keyword = ""
        for keyword, kind in _ROOM_DEVICE_HINTS.items():
            if keyword in text:
                entity = kind
                matched_keyword = keyword
                break
        if not entity:
            entity = _ACTION_DEFAULT_ENTITY.get(action, "device")

        # 2. 抽取房间名
        room = self._extract_room(text)

        # 3. 抽取设备引用：取包含设备关键词的「最长中文连续片段」。
        #    优先用别名（如果能匹配整段），否则拼接「房间 + 关键词」。
        entity_ref = ""
        if matched_keyword:
            mention = self._find_mention(text, matched_keyword, room)
            entity_ref = mention

        # 4. 别名解析（命中时替换 entity_ref）
        if self._alias_index is not None and entity_ref:
            canonical_device = self._alias_index.resolve_device(entity_ref)
            if canonical_device:
                entity_ref = canonical_device
            if room:
                canonical_room = self._alias_index.resolve_room(room)
                if canonical_room and not self._alias_index.has_conflict(room):
                    room = canonical_room

        # 5. 如果 entity 仍是默认 device，但 entity_ref 为空 → 拒识信号
        if entity == "device" and not entity_ref:
            return "device", "", params

        # 6. 抽取数值参数
        temp_match = _TEMP_RE.search(text)
        if temp_match:
            params["temperature"] = float(temp_match.group(1))
        percent_match = _PERCENT_RE.search(text)
        if percent_match:
            params["position"] = int(float(percent_match.group(1)))

        return entity, entity_ref, params

    def _extract_room(self, text: str) -> str:
        """抽取「客厅 / 卧室 / 宝宝房」等房间名。

        仅做轻量启发式：以「的 / 里」等停用词为分隔符，取其前的中文连续片段。
        实际项目可在此处接入家庭房间词典（见 ``AliasIndex``）。
        """
        # 抽取出「X 房」类短语里的 X
        m = re.search(r"([\u4e00-\u9fa5A-Za-z0-9]{1,8})房", text)
        if m:
            return m.group(1)
        # 抽取出「X 厅」类短语里的 X
        m = re.search(r"([\u4e00-\u9fa5A-Za-z0-9]{1,8})厅", text)
        if m:
            return m.group(1)
        # 抽取出「客厅 / 卧室 / 主卧 / 厨房 / 餐厅 / 书房」等无后缀的房间
        m = re.search(
            r"(客厅|卧室|主卧|次卧|厨房|餐厅|书房|卫浴|浴室|玄关|阳台|储物间|衣帽间|室内)",
            text,
        )
        if m:
            return m.group(1)
        return ""

    def _find_mention(self, text: str, keyword: str, room: str) -> str:
        """在 ``text`` 中找「含设备关键词 ``keyword`` 的最长连续片段」。

        目的：保留用户在文本里使用的原始表述（如「大灯」、「宝宝房灯」，
        别名索引会拿到「大灯」去反查），而不是只返回设备类型名。

        算法：

        1. 找 ``keyword`` 在 ``text`` 中所有出现位置。
        2. 以每个位置为中心，向左扩张：只要左边字符是中文 / 字母 / 数字
           且不属于动作 / 场景词，就拼接到片段。
        3. 过滤中间的停用词（「的」「里」）。
        4. 选所有候选中最长的一个。
        """
        candidates: list[str] = []
        noise_chars = set("的里面中内上")
        stop_chars = set("打开了关关闭调到开启动开启亮起来帮")
        for match in re.finditer(re.escape(keyword), text):
            start = match.start()
            end = match.end()
            # 向左扩张
            left = start
            while left > 0 and text[left - 1] not in stop_chars:
                ch = text[left - 1]
                if "\u4e00" <= ch <= "\u9fff" or ch.isalnum():
                    left -= 1
                else:
                    break
            candidate = text[left:end]
            # 过滤 noise
            candidate = "".join(c for c in candidate if c not in noise_chars)
            if (candidate and candidate != keyword) or (
                candidate == keyword and not room
            ):
                candidates.append(candidate)
        if not candidates:
            if room:
                return f"{room}{keyword}"
            return keyword
        # 选最长候选
        return max(candidates, key=len)

    def _domain_of_entity(self, entity: str) -> str:
        """根据设备类型反查领域标签。"""
        for domain, keywords in DOMAIN_KEYWORDS.items():
            if any(kw in entity or entity in kw for kw in keywords):
                return domain
        return "device"

    def _elapsed_ms(self) -> int:
        return int((time.perf_counter() - self._started_at) * 1000)

    def _over_budget(self, budget_ms: int) -> bool:
        return self._elapsed_ms() > budget_ms

    # parse() 入口会设置该值，所有 _elapsed_ms 调用都相对此值
    _started_at: float = 0.0


# ---------------------------------------------------------------------------
# 便捷入口
# ---------------------------------------------------------------------------


_CHINESE_DIGITS: dict[str, int] = {
    "零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9,
}
_CHINESE_UNITS: dict[str, int] = {
    "十": 10, "百": 100, "千": 1000, "万": 10000,
}


def _parse_chinese_number(text: str) -> int:
    """将「十」「十二」「一百二十三」等中文数字转成 int。

    仅支持 P0 必需的范围（0 ~ 9999）；超出范围或不可解析时返回 1 作为
    保守默认，避免「十分钟后」被静默丢弃。
    """
    if not text:
        return 1
    # 纯阿拉伯数字快路径
    if text.isdigit():
        return int(text)
    result = 0
    current = 0
    for ch in text:
        if ch in _CHINESE_DIGITS:
            current = _CHINESE_DIGITS[ch]
        elif ch in _CHINESE_UNITS:
            unit = _CHINESE_UNITS[ch]
            if current == 0:
                current = 1
            result += current * unit
            current = 0
        else:
            return 1
    result += current
    return result if result > 0 else 1


_default_engine: RuleEngine | None = None


def get_rule_engine() -> RuleEngine:
    """获取进程级单例 ``RuleEngine``。

    当前实现无状态；保留单例便于后续挂载别名缓存。
    """
    global _default_engine
    if _default_engine is None:
        _default_engine = RuleEngine()
    return _default_engine
