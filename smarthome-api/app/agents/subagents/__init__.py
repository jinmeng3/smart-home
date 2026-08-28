"""面向智能家居领域的子 Agent 基础设施。

P0 在 ``subagents/router.py`` 的关键词路由基础上，新增漏斗式分层路由
（funnel routing）：

- 规则层（Rule Layer）：确定性意图解析 + 置信度打分（``rule_engine``）
- 上下文层（Context Layer）：多轮 / 指代消解（``context_engine``）
- 路由器（Funnel Router）：按置信度 / 多轮信号决定进入哪一层（``funnel_router``）

子 Agent 一律为只读（或产出写提案），写操作必须回流主图的风险审批链路。
"""

from app.agents.subagents.contracts import SubAgentInput, SubAgentOutput
from app.agents.subagents.context_engine import (
    ContextEngine,
    ContextResolution,
    get_context_engine,
    reset_context_engine,
)
from app.agents.subagents.factory import build_subagent, run_subagent
from app.agents.subagents.funnel_router import (
    LAYER_CONTEXT,
    LAYER_DIRECT,
    LAYER_FALLBACK,
    LAYER_RULE,
    FunnelRouter,
    RouteResult,
    SessionState,
    get_funnel_router,
    reset_funnel_router,
)
from app.agents.subagents.router import (
    DELEGATABLE_DOMAINS,
    DELEGATABLE_READ_ONLY_DOMAINS,
    DELEGATABLE_WRITE_DOMAINS,
    DOMAIN_KEYWORDS,
    is_write_domain,
    resolve_delegated_domain,
    route_intent,
)
from app.agents.subagents.rule_engine import (
    AliasIndex,
    RuleEngine,
    RuleParseResult,
    WriteProposal,
    get_rule_engine,
)

__all__ = [
    "DELEGATABLE_DOMAINS",
    "DELEGATABLE_READ_ONLY_DOMAINS",
    "DELEGATABLE_WRITE_DOMAINS",
    "DOMAIN_KEYWORDS",
    "LAYER_CONTEXT",
    "LAYER_DIRECT",
    "LAYER_FALLBACK",
    "LAYER_RULE",
    "AliasIndex",
    "ContextEngine",
    "ContextResolution",
    "FunnelRouter",
    "RouteResult",
    "RuleEngine",
    "RuleParseResult",
    "SessionState",
    "SubAgentInput",
    "SubAgentOutput",
    "WriteProposal",
    "build_subagent",
    "get_context_engine",
    "get_funnel_router",
    "get_rule_engine",
    "is_write_domain",
    "reset_context_engine",
    "reset_funnel_router",
    "resolve_delegated_domain",
    "route_intent",
    "run_subagent",
]
