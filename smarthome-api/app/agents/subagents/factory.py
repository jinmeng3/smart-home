import asyncio
from uuid import uuid4

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.orm import Session

from app.agents.context import AgentContext
from app.agents.graph import build_graph
from app.agents.subagents.contracts import SubAgentOutput
from app.agents.tools import get_domain_tools


def build_subagent(
    domain: str,
    context: AgentContext,
    db: Session,
    model: BaseChatModel,
) -> CompiledStateGraph:
    """构建指定领域的只读子 Agent。

    复用主图 ``build_graph``：只读窄图只包含该领域的查询 / 预览工具，
    写工具不在其中，因此 ``should_continue`` 永远不会进入 ``risk_check``。
    """
    tools = get_domain_tools(domain, context, db)
    return build_graph(
        model=model,
        tools=tools,
        db=db,
        tools_enabled=True,
    )


async def run_subagent(
    domain: str,
    context: AgentContext,
    db: Session,
    model: BaseChatModel,
    task: str,
    *,
    system_prompt: str = "",
    recursion_limit: int = 10,
    timeout_seconds: float = 8.0,
) -> SubAgentOutput:
    """运行一次只读子 Agent 并返回结构化结果。

    失败不向上抛异常，而是返回 ``fallback_needed=True`` 的
    ``SubAgentOutput``，由主图回退到 general 兜底。
    """
    graph = build_subagent(domain, context, db, model)

    initial = {
        "messages": [
            SystemMessage(
                content=system_prompt
                or f"你是{domain}领域的智能家居子助手，只回答与当前家庭相关的问题。"
            ),
            HumanMessage(content=task),
        ],
        "context": context,
        "run_id": f"sub-{uuid4().hex}",
        "rounds": 0,
        "model_name": getattr(model, "model_name", "") or "",
    }
    config: RunnableConfig = {"recursion_limit": recursion_limit}

    try:
        result = await asyncio.wait_for(
            graph.ainvoke(initial, config=config),
            timeout=timeout_seconds,
        )
    except TimeoutError:
        return SubAgentOutput(
            domain=domain, response_text="", fallback_needed=True, error="timeout"
        )
    except Exception as exc:  # noqa: BLE001  # 子 Agent 失败回退，不中断主流程
        return SubAgentOutput(
            domain=domain, response_text="", fallback_needed=True, error=str(exc)
        )

    response_text = ""
    for message in reversed(result.get("messages", [])):
        if isinstance(message, AIMessage) and message.content:
            response_text = str(message.content)
            break

    return SubAgentOutput(domain=domain, response_text=response_text)
