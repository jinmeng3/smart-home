
from app.schemas.sse import AgentEvent
from app.utils.json import dump_json


def encode_sse_event(event: AgentEvent) -> str:
    data = event.model_dump(mode="json", exclude={"event"})
    return f"event: {event.event}\ndata: {dump_json(data)}\n\n"
