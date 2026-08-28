"""JSON 序列化 / 反序列化常用辅助。

收口后端两处重复习惯：

- 序列化默认 ``ensure_ascii=False``，对应原来散落各处的
  ``json.dumps(obj, ensure_ascii=False)``。
- 安全解析：空值或解析失败回退默认值，对应原来的 ``parse_json_list`` 等。
"""
import json
import re
from typing import Any


def dump_json(obj: Any, **kwargs) -> str:
    """序列化对象为 JSON 字符串，默认 ``ensure_ascii=False``。"""
    kwargs.setdefault("ensure_ascii", False)
    return json.dumps(obj, **kwargs)


def parse_json(value: str | None, default: Any = None) -> Any:
    """安全解析 JSON 字符串，为空或解析失败时返回 ``default``。"""
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def parse_json_list(value: str | None) -> list:
    """解析 JSON 列表字符串，失败或非列表时返回空列表。"""
    result = parse_json(value, default=[])
    return result if isinstance(result, list) else []


def extract_json(content: str) -> dict | None:
    """从模型输出中抠出 JSON 对象（兼容 Markdown ```json 代码块包裹）。"""
    if not content:
        return None
    text = content.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None
