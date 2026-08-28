import json
from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CURRENT_USER_DEPENDENCY, DB_DEPENDENCY
from app.models.chat import ChatSession
from app.models.membership import HouseholdMembership
from app.models.user import User
from app.models.user_preferences import UserPreferences


@dataclass(frozen=True, slots=True)
class AgentContext:
    user_id: int
    household_id: int
    session_id: int
    auto_execute_low_risk: bool
    confirm_high_risk: bool
    language: str = "zh-CN"
    detail_level: int = 70
    tools_enabled: bool = True


def agent_context(
    household_id: int,
    session_id: int,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
    *,
    tools_enabled: bool = True,
) -> AgentContext:
    membership = db.scalar(
        select(HouseholdMembership).where(
            HouseholdMembership.user_id == current_user.id,
            HouseholdMembership.household_id == household_id,
        )
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该家庭"
        )
    session = db.scalar(
        select(ChatSession).where(
            ChatSession.id == session_id, ChatSession.user_id == current_user.id
        )
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    if session.household_id is not None and session.household_id != household_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="会话不属于该家庭"
        )
    user_preferences = db.scalar(
        select(UserPreferences).where(UserPreferences.user_id == current_user.id)
    )
    if user_preferences is None:
        auto_execute_low_risk = False
        confirm_high_risk = True
        language = "zh-CN"
        detail_level = 70
    else:
        try:
            data = json.loads(user_preferences.preferences_json)
            # 偏好实际以 camelCase 存储（PreferencesSchema 使用 alias 序列化），兼容历史 snake_case
            ai = data.get("aiAssistant", data.get("ai", {}))
            if not isinstance(ai, dict):
                raise TypeError("ai 偏好必须是对象")
            auto_value = ai.get(
                "autoExecuteLowRisk", ai.get("auto_execute_low_risk", False)
            )
            confirm_value = ai.get("confirmHighRisk", ai.get("confirm_high_risk", True))
            language_value = ai.get("language", "zh-CN")
            detail_value = ai.get("detailLevel", ai.get("detail_level", 70))
            auto_execute_low_risk = (
                auto_value if isinstance(auto_value, bool) else False
            )
            confirm_high_risk = (
                confirm_value if isinstance(confirm_value, bool) else True
            )
            language = language_value if isinstance(language_value, str) else "zh-CN"
            detail_level = detail_value if isinstance(detail_value, int) else 70
        except (json.JSONDecodeError, AttributeError, TypeError):
            auto_execute_low_risk = False
            confirm_high_risk = True
            language = "zh-CN"
            detail_level = 70

    return AgentContext(
        user_id=current_user.id,
        household_id=household_id,
        session_id=session_id,
        auto_execute_low_risk=auto_execute_low_risk,
        confirm_high_risk=confirm_high_risk,
        language=language,
        detail_level=detail_level,
        tools_enabled=tools_enabled,
    )
