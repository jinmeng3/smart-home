"""面向智能家居领域的子 Agent 基础设施。

P0 只读原型：提供子 Agent 契约、意图路由、领域工具集与子图构建工厂。
子 Agent 一律为只读（或产出写提案），写操作必须回流主图的风险审批链路。
"""

from app.agents.subagents.contracts import SubAgentInput, SubAgentOutput
from app.agents.subagents.factory import build_subagent, run_subagent
from app.agents.subagents.router import (
    DELEGATABLE_DOMAINS,
    DELEGATABLE_READ_ONLY_DOMAINS,
    DELEGATABLE_WRITE_DOMAINS,
    DOMAIN_KEYWORDS,
    is_write_domain,
    resolve_delegated_domain,
    route_intent,
)

__all__ = [
    "DELEGATABLE_DOMAINS",
    "DELEGATABLE_READ_ONLY_DOMAINS",
    "DELEGATABLE_WRITE_DOMAINS",
    "DOMAIN_KEYWORDS",
    "SubAgentInput",
    "SubAgentOutput",
    "build_subagent",
    "is_write_domain",
    "resolve_delegated_domain",
    "route_intent",
    "run_subagent",
]
