import json

from app.schemas.sse import AgentEvent


def encode_sse_event(event: AgentEvent) -> str:
    data = event.model_dump(mode="json", exclude={"event"})
    return f"event: {event.event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
