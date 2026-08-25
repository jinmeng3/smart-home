"""领域子 Agent 定义。"""

from app.agents.subagents.domains.automation import AUTOMATION_SYSTEM_PROMPT
from app.agents.subagents.domains.device import (
    DEVICE_SYSTEM_PROMPT,
    build_device_subagent,
)
from app.agents.subagents.domains.scene import SCENE_SYSTEM_PROMPT
from app.agents.subagents.domains.security import SECURITY_SYSTEM_PROMPT

__all__ = [
    "AUTOMATION_SYSTEM_PROMPT",
    "DEVICE_SYSTEM_PROMPT",
    "SCENE_SYSTEM_PROMPT",
    "SECURITY_SYSTEM_PROMPT",
    "build_device_subagent",
]
