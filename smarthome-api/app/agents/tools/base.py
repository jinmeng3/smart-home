from collections.abc import Callable
from typing import Any

from app.agents.context import AgentContext
from langchain_core.tools import tool
from pydantic import BaseModel
from sqlalchemy.orm import Session


def build_query_tool(
    name: str,
    description: str,
    args_schema: type[BaseModel],
    context: AgentContext,
    db: Session,
    handler: Callable[..., Any],
):
    @tool(name, description=description, args_schema=args_schema)
    def _run(**kwargs: Any) -> Any:
        return handler(db=db, context=context, **kwargs)

    return _run
