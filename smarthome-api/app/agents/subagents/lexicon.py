"""规则层词典（Lexicon）：把"业务词汇"从解析代码里剥离出来。

设计目标
--------
``RuleEngine`` 原先把设备关键词 / 动作触发词 / 场景短语直接写死在模块常量里，
新增一个设备类型或场景触发语就必须改源码。本模块把这些词汇收敛成一个
:class:`RuleLexicon` 数据对象：

- **默认值仍在代码里**——中文词表可读性高，放 env 里反而难维护；
- **可通过 ``.env`` 增量扩充**——``RULE_LEXICON_EXTRA_*`` 系列配置与默认值
  **合并**（不是替换），部署方只需声明新增的词，不必重抄全表；
- **正则惰性编译**——词表可配置后不能再在模块加载时编译，改为
  ``cached_property``，每个 lexicon 实例只编译一次。

合并语义
--------
``extra_*`` 一律是"追加"：

- ``dict`` 类型（设备提示 / 场景短语）按 key 合并，**同 key 时 extra 覆盖默认**；
- ``tuple`` 类型（动作触发词）默认值在前、extra 在后**追加**，
  顺序即匹配优先级，因此追加项不会抢占已有词的优先级。

**不支持删除**默认词条——需要删除时请直接改本文件的默认值，避免"配置里悄悄
关掉一个业务能力"这种难以排查的状态。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import cached_property, lru_cache
from typing import Any

# === 结构性正则（与词表无关，不可配置）===

# 这三个正则匹配的是"数值格式"而不是业务词汇，因此保持模块级常量：
# 换一个家庭 / 换一门语言，"26度" 的写法也不会变成别的结构。
NUMBER_RE = re.compile(r"(-?\d+(?:\.\d+)?)")
TEMP_RE = re.compile(r"(-?\d+(?:\.\d+)?)\s*(?:度|℃|°C|°|C)(?!\w)", re.IGNORECASE)
PERCENT_RE = re.compile(r"(-?\d+(?:\.\d+)?)\s*(?:%|百分之|成)(?!\w)")

# 房间名抽取：「X房」/「X厅」/ 固定房间词。属于中文构词规则，非业务词汇。
#
# 房间前缀最低 2 个汉字，避免「客」单独被「厅」字捕获（贪婪退化为1字）。
ROOM_SUFFIX_FANG_RE = re.compile(r"([一-龥A-Za-z0-9]{2,8})房")
ROOM_SUFFIX_TING_RE = re.compile(r"([一-龥A-Za-z0-9]{2,8})厅")
ROOM_LITERAL_RE = re.compile(
    r"(客厅|卧室|主卧|次卧|厨房|餐厅|书房|卫浴|浴室|玄关|阳台|储物间|衣帽间|室内)"
)

# 简单查询的三类目标（时钟 / 温度 / 湿度）。
QUERY_CLOCK_RE = re.compile(r"几[点时](\d+)?|现在时间|当前时间")
QUERY_TEMPERATURE_RE = re.compile(r"温度|几度|多暖|多冷")
QUERY_HUMIDITY_RE = re.compile(r"湿度|干不干|潮不潮")

# 快捷自动化的延时表达（支持阿拉伯数字与中文数字）。
SCHEDULE_DELAY_RE = re.compile(
    r"(\d+|[一两二三四五六七八九十百千]+)\s*(分钟|秒钟|秒|小时|分)(?:之?后|再)|"
    r"等(\d+|[一两二三四五六七八九十百千]+)\s*(分钟|秒钟|秒|小时|分)"
)

# 延时单位 → 秒数倍率。
DELAY_UNIT_SECONDS: dict[str, int] = {
    "秒": 1,
    "秒钟": 1,
    "分钟": 60,
    "分": 60,
    "小时": 3600,
}


# === 默认词表 ===


# 中文停用词：出现在实体前的修饰词，匹配时需要忽略。
DEFAULT_ROOM_NOISE: tuple[str, ...] = ("的", "里", "里面", "中", "内", "上")

# 设备关键词 → 设备类型。**声明顺序即匹配优先级**（首个命中即停）。
DEFAULT_DEVICE_HINTS: dict[str, str] = {
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
DEFAULT_ACTION_DEFAULT_ENTITY: dict[str, str] = {
    "on": "device",
    "off": "device",
    "set_temperature": "air_conditioner",
    "set_position": "curtain",
}

# 「打开 / 关闭」类动作的中文触发词。
DEFAULT_TURN_ON_PATTERNS: tuple[str, ...] = (
    "打开",
    "开",
    "启动",
    "开启",
    "亮一下",
    "亮起来",
    "开一下",
    "帮我开",
)
DEFAULT_TURN_OFF_PATTERNS: tuple[str, ...] = (
    "关闭",
    "关",
    "关上",
    "关掉",
    "熄",
    "关一下",
    "帮我关",
)

# 「设置」类动作的触发词。
DEFAULT_SET_TEMP_PATTERNS: tuple[str, ...] = (
    "调到",
    "设置成",
    "设为",
    "设置到",
    "调成",
    "调至",
    "设定",
)
DEFAULT_SET_POSITION_PATTERNS: tuple[str, ...] = (
    "开到",
    "关到",
    "调到",
    "设置到",
    "开合",
    "拉到",
)

# 「查询」类动作的触发词。
DEFAULT_QUERY_STATE_PATTERNS: tuple[str, ...] = (
    "现在",
    "多少",
    "几度",
    "怎么样",
    "如何",
    "状态",
    "开没开",
    "开着没",
)

# 预设场景意图 key → 触发短语。
#
# .. important::
#     key 是"场景意图标识"，**不是数据库里的 ``Scene.id``**。
#     ``Scene.id`` 是全局唯一的 String(64) 主键（通常是生成值），
#     而且同一个"回家"场景在不同家庭里 id 各不相同。
#     真实 id 由 ``rule_layer._resolve_scene`` 在**当前家庭范围内**反查。
DEFAULT_SCENE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "home": ("我回来了", "回来了", "回家", "到家了"),
    "leave": ("我出门了", "出门了", "离家", "走了", "外出了"),
    "sleep": ("睡觉了", "我要睡了", "晚安", "去睡"),
    "wake": ("起床了", "早安", "起来了", "醒来了"),
    "movie": ("观影模式", "看电影", "开始观影", "电影模式"),
    "reading": ("阅读模式", "我要看书", "开始阅读"),
    "cooking": ("做饭了", "烹饪模式", "开始做饭"),
}

# 场景意图 key → 候选场景名关键词，用于在家庭场景表里反查真实 ``Scene.id``。
#
# 匹配策略见 ``rule_layer._resolve_scene``：先精确名称，再包含匹配；
# 命中多个场景时视为歧义，不执行而是交由上层追问。
DEFAULT_SCENE_NAME_HINTS: dict[str, tuple[str, ...]] = {
    "home": ("回家", "到家", "归家"),
    "leave": ("离家", "出门", "外出"),
    "sleep": ("睡眠", "晚安", "就寝", "睡觉"),
    "wake": ("起床", "早安", "啮醒"),
    "movie": ("观影", "电影", "影院"),
    "reading": ("阅读", "看书", "学习"),
    "cooking": ("烹饪", "做饭", "厨房"),
}

# 复合 / 决策型意图信号：命中即让规则层拒识，交给兜底层（LLM）。
DEFAULT_COMPOSITE_SIGNALS: tuple[str, ...] = (
    "顺便",
    "还有",
    "另外",
    "同时",
    "再帮我",
    "然后",
)
DEFAULT_DECISION_SIGNALS: tuple[str, ...] = (
    "决定",
    "要不要",
    "看看",
    "需不需要",
    "是不是要",
)

# ``_find_mention`` 向左扩张时的边界字符（动作词尾字，遇到即停）。
DEFAULT_MENTION_STOP_CHARS = "打开了关关闭调到开启动开启亮起来帮我把请将"
# ``_find_mention`` 结果中要剔除的噪音字。
DEFAULT_MENTION_NOISE_CHARS = "的里面中内上把请将"


# === Lexicon 数据对象 ===


@dataclass(frozen=True)
class RuleLexicon:
    """一份完整的规则层词表 + 由它派生的编译正则。

    正则用 ``cached_property`` 惰性编译：``frozen=True`` 不影响
    ``cached_property`` 写入（它直接写 ``__dict__``，不走 ``__setattr__``）。
    """

    room_noise: tuple[str, ...] = DEFAULT_ROOM_NOISE
    device_hints: dict[str, str] = field(
        default_factory=lambda: dict(DEFAULT_DEVICE_HINTS)
    )
    action_default_entity: dict[str, str] = field(
        default_factory=lambda: dict(DEFAULT_ACTION_DEFAULT_ENTITY)
    )
    turn_on_patterns: tuple[str, ...] = DEFAULT_TURN_ON_PATTERNS
    turn_off_patterns: tuple[str, ...] = DEFAULT_TURN_OFF_PATTERNS
    set_temp_patterns: tuple[str, ...] = DEFAULT_SET_TEMP_PATTERNS
    set_position_patterns: tuple[str, ...] = DEFAULT_SET_POSITION_PATTERNS
    query_state_patterns: tuple[str, ...] = DEFAULT_QUERY_STATE_PATTERNS
    scene_keywords: dict[str, tuple[str, ...]] = field(
        default_factory=lambda: dict(DEFAULT_SCENE_KEYWORDS)
    )
    scene_name_hints: dict[str, tuple[str, ...]] = field(
        default_factory=lambda: dict(DEFAULT_SCENE_NAME_HINTS)
    )
    composite_signals: tuple[str, ...] = DEFAULT_COMPOSITE_SIGNALS
    decision_signals: tuple[str, ...] = DEFAULT_DECISION_SIGNALS
    mention_stop_chars: str = DEFAULT_MENTION_STOP_CHARS
    mention_noise_chars: str = DEFAULT_MENTION_NOISE_CHARS

    # ---- 派生正则 ----

    @cached_property
    def turn_on_re(self) -> re.Pattern[str]:
        return re.compile("|".join(self.turn_on_patterns))

    @cached_property
    def turn_off_re(self) -> re.Pattern[str]:
        return re.compile("|".join(self.turn_off_patterns))

    @cached_property
    def set_temp_re(self) -> re.Pattern[str]:
        return re.compile("|".join(self.set_temp_patterns))

    @cached_property
    def set_position_re(self) -> re.Pattern[str]:
        return re.compile("|".join(self.set_position_patterns))

    @cached_property
    def query_state_re(self) -> re.Pattern[str]:
        return re.compile("|".join(self.query_state_patterns))

    @cached_property
    def room_noise_re(self) -> re.Pattern[str]:
        return re.compile(
            "(" + "|".join(re.escape(word) for word in self.room_noise) + ")"
        )

    @cached_property
    def mention_stop_char_set(self) -> frozenset[str]:
        return frozenset(self.mention_stop_chars)

    @cached_property
    def mention_noise_char_set(self) -> frozenset[str]:
        return frozenset(self.mention_noise_chars)

    @cached_property
    def all_composite_signals(self) -> tuple[str, ...]:
        """复合信号 + 决策信号的合集（``_is_composite_intent`` 一次遍历用）。"""
        return (*self.composite_signals, *self.decision_signals)


# === 合并与工厂 ===


def _merge_str_map(
    default: dict[str, str], extra: dict[str, str] | None
) -> dict[str, str]:
    """字符串映射合并：默认值在前保持顺序，extra 同 key 覆盖、新 key 追加。"""
    merged = dict(default)
    if extra:
        merged.update({str(k): str(v) for k, v in extra.items()})
    return merged


def _merge_phrase_map(
    default: dict[str, tuple[str, ...]], extra: dict[str, Any] | None
) -> dict[str, tuple[str, ...]]:
    """短语表合并：同 key 的短语**追加去重**，新 key 直接加入。"""
    merged = {key: tuple(value) for key, value in default.items()}
    if not extra:
        return merged
    for key, phrases in extra.items():
        if isinstance(phrases, str):
            phrases = [phrases]
        added = tuple(str(p) for p in phrases if str(p).strip())
        existing = merged.get(str(key), ())
        # 去重但保序：已存在的短语不重复追加
        merged[str(key)] = existing + tuple(p for p in added if p not in existing)
    return merged


def _merge_patterns(
    default: tuple[str, ...], extra: list[str] | None
) -> tuple[str, ...]:
    """触发词合并：默认值在前（优先级更高），extra 去重后追加。"""
    if not extra:
        return default
    return default + tuple(
        str(item) for item in extra if str(item).strip() and str(item) not in default
    )


def build_lexicon(settings: Any | None = None) -> RuleLexicon:
    """按 ``.env`` 里的 ``RULE_LEXICON_EXTRA_*`` 增量构建词表。

    ``settings`` 为 None 时读取 ``get_settings()``；配置层异常时退回纯默认词表，
    保证规则层永远可用（词表缺失不应让整个 Agent 不可用）。
    """
    if settings is None:
        try:
            from app.core.config import get_settings

            settings = get_settings()
        except Exception:  # noqa: BLE001  # 配置不可用时退回内置默认词表
            return RuleLexicon()

    def cfg(name: str) -> Any:
        return getattr(settings, name, None)

    return RuleLexicon(
        device_hints=_merge_str_map(
            DEFAULT_DEVICE_HINTS, cfg("rule_lexicon_extra_device_hints")
        ),
        turn_on_patterns=_merge_patterns(
            DEFAULT_TURN_ON_PATTERNS, cfg("rule_lexicon_extra_turn_on")
        ),
        turn_off_patterns=_merge_patterns(
            DEFAULT_TURN_OFF_PATTERNS, cfg("rule_lexicon_extra_turn_off")
        ),
        query_state_patterns=_merge_patterns(
            DEFAULT_QUERY_STATE_PATTERNS, cfg("rule_lexicon_extra_query_state")
        ),
        scene_keywords=_merge_phrase_map(
            DEFAULT_SCENE_KEYWORDS, cfg("rule_lexicon_extra_scene_keywords")
        ),
        scene_name_hints=_merge_phrase_map(
            DEFAULT_SCENE_NAME_HINTS, cfg("rule_lexicon_extra_scene_name_hints")
        ),
    )


@lru_cache(maxsize=1)
def get_lexicon() -> RuleLexicon:
    """进程级缓存的词表实例（正则只编译一次）。"""
    return build_lexicon()


def reset_lexicon() -> None:
    """清空词表缓存（测试 / 配置热更后调用）。"""
    get_lexicon.cache_clear()
