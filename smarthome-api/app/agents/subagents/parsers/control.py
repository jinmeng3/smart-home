"""直接控制解析器：「打开客厅灯」「空调调到 26 度」「窗帘开到 50%」。

产出的 :class:`WriteProposal` **不含 device_id**——只有 ``entity_ref``
（用户原始表述或别名反查后的标准名），真实设备由 ``rule_layer`` 反查填充。
"""

from __future__ import annotations

from app.agents.subagents.parsers.base import (
    RuleContext,
    RuleParseResult,
    WriteProposal,
)
from app.agents.subagents.parsers.extract import (
    detect_action,
    domain_of_entity,
    extract_entity,
)

# 动作 → 写工具名。新增动作时在这里登记，避免散落 if/elif。
ACTION_TOOLS: dict[str, str] = {
    "on": "set_device_power",
    "off": "set_device_power",
    "set_temperature": "set_device_temperature",
    "set_position": "set_curtain_position",
}


def _build_proposal(
    action: str, text: str, params: dict
) -> WriteProposal | None:
    """按动作构造写提案；参数缺失时返回 ``None``（拒识）。"""
    tool = ACTION_TOOLS.get(action)
    if tool is None:
        return None

    if action == "on":
        return WriteProposal(tool=tool, args={"power": "on"})
    if action == "off":
        return WriteProposal(tool=tool, args={"power": "off"})
    if action == "set_temperature":
        temp = params.get("temperature")
        if temp is None:
            return None
        return WriteProposal(tool=tool, args={"temperature": float(temp)})
    if action == "set_position":
        # 未给出具体百分比时：「开」默认全开，其余默认全关
        position = params.get("position", 100 if "开" in text else 0)
        return WriteProposal(tool=tool, args={"position": int(position)})
    return None


class ControlParser:
    """设备直接控制。"""

    name = "control"
    priority = 40

    def try_parse(self, ctx: RuleContext) -> RuleParseResult | None:
        text = ctx.text
        action = detect_action(text, ctx.lexicon)
        if action is None:
            return None

        entity, entity_ref, params = extract_entity(
            text, action, ctx.lexicon, ctx.alias_index
        )
        # 解析不到实体引用（如只说「打开」）→ 拒识，避免误触执行
        if not entity_ref:
            return None

        proposal = _build_proposal(action, text, params)
        if proposal is None:
            return None

        # 当前实现走到这里 entity_ref 必然非空，因此一律高置信度。
        # 未来若引入"别名模糊匹配"（如 embedding 召回但相似度中等），
        # 应在此处降级为 ctx.conf_mid 并置 needs_clarification=True。
        confidence = ctx.conf_high
        needs_clarification = confidence < ctx.conf_high

        return RuleParseResult(
            matched=True,
            intent="control",
            domain=domain_of_entity(entity),
            confidence=confidence,
            action=action,
            entity=entity,
            entity_ref=entity_ref,
            params=params,
            write_proposals=(proposal,),
            needs_clarification=needs_clarification,
            clarification_prompt=(
                f"请确认要操作的目标是「{entity_ref or entity}」吗？"
                if needs_clarification
                else ""
            ),
            elapsed_ms=ctx.elapsed_ms(),
        )
