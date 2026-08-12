from collections.abc import Callable
from typing import Any

from app.agents.context import AgentContext
from langchain_core.tools import tool
from pydantic import BaseModel
from sqlalchemy.orm import Session


def _cap_results(result: Any, max_results: int) -> Any:
    """限制消息数量"""
    if isinstance(result, list) and len(result) > max_results:
        return result[:max_results]
    return result


def build_query_tool(
    name: str,
    description: str,
    args_schema: type[BaseModel],
    context: AgentContext,
    db: Session,
    handler: Callable[..., Any],
    *,
    max_results: int | None = None,
):
    from app.core.config import get_settings

    actual_max_results = (
        max_results
        if max_results is not None
        else get_settings().agent_tool_result_max_length
    )

    @tool(name, description=description, args_schema=args_schema)
    def _run(**kwargs: Any) -> Any:
        return _cap_results(
            handler(db=db, context=context, **kwargs), actual_max_results
        )

    return _run
