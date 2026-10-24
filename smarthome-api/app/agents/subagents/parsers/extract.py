"""从中文文本里抽取动作 / 房间 / 实体引用 / 数值参数的纯函数。

这些函数原先是 ``RuleEngine`` 的私有方法，抽成模块级纯函数后：

- 各 parser 可以直接复用，不必继承或持有引擎实例；
- 词表通过参数注入（``lexicon``），便于测试时传自定义词表；
- 无隐藏状态，行为只由入参决定。
"""

from __future__ import annotations

import re
from typing import Any

from app.agents.subagents.alias_index import AliasIndex
from app.agents.subagents.domain_router import DOMAIN_KEYWORDS
from app.agents.subagents.lexicon import (
    PERCENT_RE,
    ROOM_LITERAL_RE,
    ROOM_SUFFIX_FANG_RE,
    ROOM_SUFFIX_TING_RE,
    TEMP_RE,
    RuleLexicon,
)

# === 动作识别 ===


def detect_action(text: str, lexicon: RuleLexicon) -> str | None:
    """识别动作枚举；无法识别时返回 ``None``。

    顺序：先识别「调温 / 调位置」这类带数值的设置动作，避免被「开」这种
    单字动作误判（"空调调到26度" 里既有"调到"也有"开"的可能）。
    """
    if lexicon.set_temp_re.search(text) and TEMP_RE.search(text):
        return "set_temperature"
    if lexicon.set_position_re.search(text) and PERCENT_RE.search(text):
        return "set_position"
    if lexicon.turn_off_re.search(text):
        return "off"
    if lexicon.turn_on_re.search(text):
        return "on"
    return None


# === 房间 / 实体抽取 ===


def extract_room(text: str) -> str:
    """抽取「客厅 / 卧室 / 宝宝房」等房间名；未命中返回空字符串。

    仅做轻量启发式（中文构词规则），不查家庭房间表——真实房间名由
    :class:`AliasIndex` 反查。

    顺序：
      1. 固定词表优先（客厅/卧室/...）—— 避免「客厅温度」被「厅」字 regex 贪婪匹配为「客」。
      2. 「X房」/「X厅」启发式补充。
      3. 「X房」中限定「没有/不要/不需要」等否定前缀不算房间。
    """
    # 1. 固定词表优先
    match = ROOM_LITERAL_RE.search(text)
    if match:
        return match.group(1)
    # 2. 「X房」启发式（要求「没有」等否定词后的「房」不算）
    match = ROOM_SUFFIX_FANG_RE.search(text)
    if match:
        prefix = match.group(1)
        # 「没有房」/「不要房」/「不需要房」类伪匹配 → 跳过
        if not prefix.endswith(("没有", "不要", "不需要", "不要", "不会")):
            return prefix
    # 3. 「X厅」启发式
    match = ROOM_SUFFIX_TING_RE.search(text)
    if match:
        return match.group(1)
    return ""


def find_mention(text: str, keyword: str, room: str, lexicon: RuleLexicon) -> str:
    """在 ``text`` 中找「含设备关键词 ``keyword`` 的最长连续片段」。

    目的：保留用户在文本里使用的原始表述（如「大灯」「宝宝房灯」，别名索引会
    拿「大灯」去反查），而不是只返回设备类型名。

    算法：

    1. 找 ``keyword`` 在 ``text`` 中所有出现位置；
    2. 以每个位置为中心向左扩张：只要左边字符是中文 / 字母 / 数字且不属于
       动作词尾字（``lexicon.mention_stop_chars``），就并入片段；
    3. 剔除片段中的噪音字（``lexicon.mention_noise_chars``，如「的」「里」）；
    4. 取所有候选中最长的一个。
    """
    candidates: list[str] = []
    noise_chars = lexicon.mention_noise_char_set
    stop_chars = lexicon.mention_stop_char_set
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
        candidate = "".join(c for c in candidate if c not in noise_chars)
        if (candidate and candidate != keyword) or (candidate == keyword and not room):
            candidates.append(candidate)
    if not candidates:
        return f"{room}{keyword}" if room else keyword
    return max(candidates, key=len)


def extract_entity(
    text: str,
    action: str,
    lexicon: RuleLexicon,
    alias_index: AliasIndex | None = None,
) -> tuple[str, str, dict[str, Any]]:
    """从原始文本里抽取 ``(entity, entity_ref, params)``。

    - ``entity``：设备类型枚举；
    - ``entity_ref``：实体引用文本（房间名 + 设备 / 别名），供上层反查真实设备；
    - ``params``：动作参数（温度 / 百分比等）。

    ``entity_ref`` 为空表示**拒识信号**——调用方应放弃本次匹配，避免误触执行。
    """
    params: dict[str, Any] = {}

    # 1. 优先识别显式的设备类型关键词（词表声明顺序即优先级）
    entity = ""
    matched_keyword = ""
    for keyword, kind in lexicon.device_hints.items():
        if keyword in text:
            entity = kind
            matched_keyword = keyword
            break
    if not entity:
        entity = lexicon.action_default_entity.get(action, "device")

    # 2. 抽取房间名
    room = extract_room(text)

    # 3. 抽取设备引用（保留用户原始表述）
    entity_ref = ""
    if matched_keyword:
        entity_ref = find_mention(text, matched_keyword, room, lexicon)

    # 4. 别名解析（命中时替换 entity_ref / room）
    if alias_index is not None and entity_ref:
        canonical_device = alias_index.resolve_device(entity_ref)
        if canonical_device:
            entity_ref = canonical_device
        if room:
            canonical_room = alias_index.resolve_room(room)
            if canonical_room and not alias_index.has_conflict(room):
                room = canonical_room

    # 5. 仍是默认 device 且没有引用 → 拒识信号
    if entity == "device" and not entity_ref:
        return "device", "", params

    # 6. 抽取数值参数
    temp_match = TEMP_RE.search(text)
    if temp_match:
        params["temperature"] = float(temp_match.group(1))
    percent_match = PERCENT_RE.search(text)
    if percent_match:
        params["position"] = int(float(percent_match.group(1)))

    return entity, entity_ref, params


# === 领域反查 ===


def domain_of_entity(entity: str) -> str:
    """根据设备类型反查领域标签；无法判定时回退 ``"device"``。"""
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(kw in entity or entity in kw for kw in keywords):
            return domain
    return "device"


# === 中文数字 ===


_CHINESE_DIGITS: dict[str, int] = {
    "零": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}
_CHINESE_UNITS: dict[str, int] = {
    "十": 10,
    "百": 100,
    "千": 1000,
    "万": 10000,
}


def parse_chinese_number(text: str) -> int:
    """将「十」「十二」「一百二十三」等中文数字转成 int。

    仅支持 0 ~ 9999；超出范围或不可解析时返回 1 作为保守默认，
    避免「十分钟后」被静默丢弃。
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
