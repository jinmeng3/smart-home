from cryptography.fernet import Fernet
from langchain_core.messages import AIMessage

from app.agents import crypto
from app.agents.graph.risk_node import risk_check
from app.agents.graph.tool_router import route_after_risk
from app.agents.redaction import redact_fields, redact_text


def test_api_key_uses_authenticated_encryption(monkeypatch):
    key = Fernet.generate_key()
    monkeypatch.setattr(crypto, "_derive_key", lambda: key)
    monkeypatch.setattr(crypto, "_decryption_fernets", lambda: [Fernet(key)])

    encrypted = crypto.encrypt_api_key("sk-secret-value")

    assert encrypted is not None
    assert encrypted != "sk-secret-value"
    assert encrypted.startswith("enc:v1:gAAAA")
    assert crypto.decrypt_api_key(encrypted) == "sk-secret-value"


def test_redaction_never_keeps_original_secret():
    secret = "sk-abcdef123456"

    assert secret not in redact_text(f"token={secret}")
    assert redact_fields({"items": [{"api_key": secret}]}) == {
        "items": [{"api_key": "<redacted>"}]
    }


def test_invalid_write_arguments_return_to_model_instead_of_interrupting():
    message = AIMessage(
        content="",
        tool_calls=[
            {
                "id": "call-1",
                "name": "create_automation",
                "args": {},
                "type": "tool_call",
            }
        ],
    )
    state = {"messages": [message], "rounds": 0, "run_id": "run-1"}

    result = risk_check(state, db=None)  # type: ignore[arg-type]
    next_state = {**state, **result}

    assert result["pending_approval"] is None
    assert result["rounds"] == 1
    assert route_after_risk(next_state) == "model"
    assert "参数校验失败" in result["messages"][0].content


def test_mixed_read_and_write_calls_are_all_answered():
    message = AIMessage(
        content="",
        tool_calls=[
            {
                "id": "call-read",
                "name": "list_rooms",
                "args": {},
                "type": "tool_call",
            },
            {
                "id": "call-write",
                "name": "delete_automation",
                "args": {"automation_id": 1},
                "type": "tool_call",
            },
        ],
    )
    state = {"messages": [message], "rounds": 0, "run_id": "run-1"}

    result = risk_check(state, db=None)  # type: ignore[arg-type]

    assert {item.tool_call_id for item in result["messages"]} == {
        "call-read",
        "call-write",
    }
    assert result["pending_approval"] is None
