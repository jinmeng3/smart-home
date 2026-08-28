from app.agents.subagents.domains.automation import AUTOMATION_SYSTEM_PROMPT
from app.agents.subagents.domains.automation_templates import (
    AUTOMATION_TEMPLATES_SYSTEM_PROMPT,
)
from app.agents.subagents.domains.device import (
    DEVICE_SYSTEM_PROMPT,
    build_device_subagent,
)
from app.agents.subagents.domains.scene import SCENE_SYSTEM_PROMPT
from app.agents.subagents.domains.security import SECURITY_SYSTEM_PROMPT
from app.agents.subagents.domains.settings_suggestions import (
    SUGGESTIONS_SYSTEM_PROMPT,
)

__all__ = [
    "AUTOMATION_SYSTEM_PROMPT",
    "AUTOMATION_TEMPLATES_SYSTEM_PROMPT",
    "DEVICE_SYSTEM_PROMPT",
    "SCENE_SYSTEM_PROMPT",
    "SECURITY_SYSTEM_PROMPT",
    "SUGGESTIONS_SYSTEM_PROMPT",
    "build_device_subagent",
]
