from app.agents.context import AgentContext
from langchain_core.tools import tool
from sqlalchemy.orm import Session


def build_tool(
    name: str,
    description: str,
    context: AgentContext,
    db: Session,
    handler,
    args_schema,
):
    @tool(name, description=description, args_schema=args_schema)
    def _run(**kwargs):
        return handler(db=db, context=context, **kwargs)

    return _run
