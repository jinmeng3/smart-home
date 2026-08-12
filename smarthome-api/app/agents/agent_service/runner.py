from collections.abc import Generator
from typing import Any, cast
from uuid import uuid4

from app.agents.events.models import (
    Error,
    MessageDelta,
    RunCompleted,
    RunStarted,
    ToolCompleted,
    ToolStarted,
)
from app.agents.events.sse import encode_sse_event
from app.agents.prompts import system_prompt
from app.agents.redaction import redact_text
from app.agents.tools import get_household_tools
from app.api.deps import get_model_cache
from app.models.chat import ChatMessage
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage


def run_agent(
    context, household_name, message, model_config, db
) -> Generator[str, None, None]:
    run_id = f"run-{uuid4().hex}"
    cache = get_model_cache()
    model = cache.get(model_config)
    tools = get_household_tools(context, db)
    agent = create_agent(model=model, tools=tools)

    yield encode_sse_event(
        RunStarted(
            event_id=f"{run_id}-start",
            run_id=run_id,
            session_id=context.session_id,
            household_id=context.household_id,
        )
    )
    sys_prompt = system_prompt(context, household_name, db)

    db.add(ChatMessage(session_id=context.session_id, role="user", content=message))
    db.commit()

    collected = ""
    call_id = 0
    messages = [SystemMessage(content=sys_prompt), HumanMessage(content=message)]
    try:
        for chunk, _metadata in agent.stream(
            input={"messages": messages}, stream_mode="messages"
        ):
            msg = cast(Any, chunk)
            tool_calls = getattr(msg, "tool_calls", None) or []
            for tool_call in tool_calls:
                call_id += 1
                tc = (
                    tool_call if isinstance(tool_call, dict) else tool_call.model_dump()
                )
                yield encode_sse_event(
                    ToolStarted(
                        event_id=f"{run_id}-tool{call_id}",
                        run_id=run_id,
                        call_id=str(tc.get("id", call_id)),
                        tool=str(tc.get("name", "unknown")),
                        summary=f"正在调用 {tc.get('name', 'unknown')}",
                    )
                )
            name = getattr(msg, "name", None)
            content = getattr(msg, "content", None)
            if name and content:
                yield encode_sse_event(
                    ToolCompleted(
                        event_id=f"{run_id}-result{call_id}",
                        run_id=run_id,
                        call_id=str(call_id),
                        tool=str(name),
                        result=redact_text(str(content))[:500],
                    )
                )
            elif content:
                collected += str(content)
                yield encode_sse_event(
                    MessageDelta(
                        event_id=f"{run_id}-{len(collected)}",
                        run_id=run_id,
                        content=str(content),
                    )
                )
    except Exception as e:  # noqa: BLE001
        yield encode_sse_event(
            Error(
                event_id=f"{run_id}-error",
                run_id=run_id,
                message=redact_text(str(e)),
                retryable=False,
            )
        )
        return

    if collected.strip():
        db.add(
            ChatMessage(
                session_id=context.session_id,
                role="assistant",
                content=collected.strip(),
            )
        )
        db.commit()
    yield encode_sse_event(
        RunCompleted(
            event_id=f"{run_id}-done", run_id=run_id, session_id=context.session_id
        )
    )
