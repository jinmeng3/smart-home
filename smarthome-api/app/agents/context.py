import json
from dataclasses import dataclass

from app.api.deps import CURRENT_USER_DEPENDENCY, DB_DEPENDENCY
from app.models.chat import ChatSession
from app.models.membership import HouseholdMembership
from app.models.user import User
from app.models.user_preferences import UserPreferences
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session


@dataclass(frozen=True, slots=True)
class AgentContext:
    user_id: int
    household_id: int
    session_id: int
    auto_execute_low_risk: bool
    confirm_high_risk: bool


def agent_context(
    household_id: int,
    session_id: int,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
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
    user_preferences = db.scalar(
        select(UserPreferences).where(UserPreferences.user_id == current_user.id)
    )
    if user_preferences is None:
        auto_execute_low_risk = False
        confirm_high_risk = True
    else:
        try:
            data = json.loads(user_preferences.preferences_json)
            ai = data.get("ai", {})
            if not isinstance(ai, dict):
                raise TypeError("ai 偏好必须是对象")
            auto_value = ai.get("auto_execute_low_risk", False)
            confirm_value = ai.get("confirm_high_risk", True)
            auto_execute_low_risk = auto_value if isinstance(auto_value, bool) else False
            confirm_high_risk = confirm_value if isinstance(confirm_value, bool) else True
        except (json.JSONDecodeError, AttributeError, TypeError):
            auto_execute_low_risk = False
            confirm_high_risk = True

    return AgentContext(
        user_id=current_user.id,
        household_id=household_id,
        session_id=session_id,
        auto_execute_low_risk=auto_execute_low_risk,
        confirm_high_risk=confirm_high_risk,
    )
