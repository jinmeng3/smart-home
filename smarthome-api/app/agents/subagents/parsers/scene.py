"""固定场景解析器：「我回来了」「晚安」「观影模式」。

场景触发短语来自 ``lexicon.scene_keywords``（可通过
``RULE_LEXICON_EXTRA_SCENE_KEYWORDS`` 追加）。

.. important::
    本层产出的 ``entity_ref`` / ``params["scene_key"]`` 是**场景意图标识**
    （``home`` / ``leave`` / ``sleep`` ...），**不是数据库里的 ``Scene.id``**。

    ``Scene.id`` 是全局唯一的 String(64) 主键，同一个"回家"场景在不同家庭里
    id 各不相同，因此规则层无法在这里写死。写提案的 ``args`` 刻意留空，
    真实 ``scene_id`` 由 ``rule_layer._resolve_scene`` 在**当前家庭范围内**
    反查后填充——与设备提案不带 ``device_id`` 是同一套约定。
"""

from __future__ import annotations

from app.agents.subagents.parsers.base import (
    RuleContext,
    RuleParseResult,
    WriteProposal,
)


class SceneParser:
    """预设场景触发。"""

    name = "scene"
    priority = 20

    def try_parse(self, ctx: RuleContext) -> RuleParseResult | None:
        text = ctx.text
        for scene_key, phrases in ctx.lexicon.scene_keywords.items():
            for phrase in phrases:
                if phrase in text:
                    return RuleParseResult(
                        matched=True,
                        intent="scene",
                        domain="scene",
                        confidence=ctx.conf_high,
                        action="trigger",
                        entity="scene",
                        # 场景意图标识，供 rule_layer 反查真实 Scene.id
                        entity_ref=scene_key,
                        params={"scene_key": scene_key, "matched_phrase": phrase},
                        # args 留空：scene_id 由执行层按家庭反查后注入
                        write_proposals=(
                            WriteProposal(tool="execute_scene", args={}),
                        ),
                        elapsed_ms=ctx.elapsed_ms(),
                    )
        return None
