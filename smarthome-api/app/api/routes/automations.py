import json
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import (
    CURRENT_USER_DEPENDENCY,
    DB_DEPENDENCY,
    HOUSEHOLD_MEMBER_DEPENDENCY,
)
from app.models.automation import Automation, AutomationTrigger
from app.models.membership import HouseholdMembership
from app.models.user import User
from app.schemas.automation import (
    AutomationCreate,
    AutomationListRead,
    AutomationRead,
    AutomationUpdate,
    BatchEnableRead,
    BatchEnableWrite,
    BatchScheduleWrite,
    EnabledRead,
    EnabledWrite,
    ExecuteRead,
    ExecuteWrite,
    ExecutionListRead,
)
from app.schemas.common import ApiResponse
from app.services.automation import (
    batch_enable,
    create_automation,
    execute_automation,
    get_automation,
    list_automations,
    list_executions,
    serialize,
    update_automation,
)

router = APIRouter(tags=["automations"])


def accessible_automation(
    db: Session, user: User, automation_id: int
) -> tuple[Automation, int]:
    household_id = db.scalar(
        select(HouseholdMembership.household_id)
        .join(Automation, Automation.household_id == HouseholdMembership.household_id)
        .where(HouseholdMembership.user_id == user.id, Automation.id == automation_id)
    )
    if household_id is None:
        raise HTTPException(status_code=404, detail="自动化规则不存在")
    return get_automation(db, automation_id, household_id), household_id


@router.get(
    "/households/{household_id}/automations",
    response_model=ApiResponse[AutomationListRead],
)
def get_automations(
    household_id: int,
    _membership=HOUSEHOLD_MEMBER_DEPENDENCY,
    keyword: str | None = None,
    trigger_type: str | None = None,
    enabled: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[AutomationListRead]:
    return ApiResponse.ok(
        list_automations(
            db, household_id, keyword, trigger_type, enabled, page, page_size
        )
    )


@router.post(
    "/households/{household_id}/automations",
    response_model=ApiResponse[AutomationRead],
    status_code=status.HTTP_201_CREATED,
)
def add_automation(
    household_id: int,
    payload: AutomationCreate,
    _membership=HOUSEHOLD_MEMBER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
    user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[AutomationRead]:
    return ApiResponse.ok(
        create_automation(db, household_id, user.id, payload), "created"
    )


@router.get("/automations/{automation_id}", response_model=ApiResponse[AutomationRead])
def read_automation(
    automation_id: int,
    db: Session = DB_DEPENDENCY,
    user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[AutomationRead]:
    automation, _ = accessible_automation(db, user, automation_id)
    return ApiResponse.ok(serialize(automation))


@router.patch(
    "/automations/{automation_id}", response_model=ApiResponse[AutomationRead]
)
def edit_automation(
    automation_id: int,
    payload: AutomationUpdate,
    db: Session = DB_DEPENDENCY,
    user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[AutomationRead]:
    _, household_id = accessible_automation(db, user, automation_id)
    return ApiResponse.ok(update_automation(db, automation_id, household_id, payload))


@router.patch(
    "/automations/{automation_id}/enabled", response_model=ApiResponse[EnabledRead]
)
def change_automation_enabled(
    automation_id: int,
    payload: EnabledWrite,
    db: Session = DB_DEPENDENCY,
    user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[EnabledRead]:
    automation, _ = accessible_automation(db, user, automation_id)
    automation.enabled = payload.enabled
    automation.version += 1
    db.commit()
    return ApiResponse.ok(EnabledRead(id=automation.id, enabled=automation.enabled))


@router.post(
    "/automations/{automation_id}/execute",
    response_model=ApiResponse[ExecuteRead],
    status_code=status.HTTP_202_ACCEPTED,
)
def run_automation(
    automation_id: int,
    payload: ExecuteWrite,
    idempotency_key: Annotated[str | None, Header()] = None,
    db: Session = DB_DEPENDENCY,
    user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[ExecuteRead]:
    automation, _ = accessible_automation(db, user, automation_id)
    return ApiResponse.ok(
        execute_automation(db, automation, payload.source, idempotency_key)
    )


@router.get(
    "/automations/{automation_id}/executions",
    response_model=ApiResponse[ExecutionListRead],
)
def get_automation_executions(
    automation_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = DB_DEPENDENCY,
    user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[ExecutionListRead]:
    automation, _ = accessible_automation(db, user, automation_id)
    return ApiResponse.ok(
        list_executions(db, automation, page, page_size, status_filter)
    )


@router.post("/automations/batch-enable", response_model=ApiResponse[BatchEnableRead])
def batch_enable_automations(
    payload: BatchEnableWrite,
    db: Session = DB_DEPENDENCY,
    user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[BatchEnableRead]:
    household_id = db.scalar(
        select(HouseholdMembership.household_id)
        .where(HouseholdMembership.user_id == user.id)
        .order_by(HouseholdMembership.id)
    )
    if household_id is None:
        raise HTTPException(status_code=403, detail="当前用户尚未加入家庭")
    return ApiResponse.ok(batch_enable(db, household_id, payload))


@router.put("/automations/schedules/batch", response_model=ApiResponse[BatchEnableRead])
def batch_schedule_automations(
    payload: BatchScheduleWrite,
    db: Session = DB_DEPENDENCY,
    user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[BatchEnableRead]:
    household_id = db.scalar(
        select(HouseholdMembership.household_id)
        .where(HouseholdMembership.user_id == user.id)
        .order_by(HouseholdMembership.id)
    )
    if household_id is None:
        raise HTTPException(status_code=403, detail="当前用户尚未加入家庭")
    rules = list(
        db.scalars(
            select(Automation).where(
                Automation.household_id == household_id,
                Automation.id.in_(payload.rule_ids),
            )
        ).all()
    )
    if len(rules) != len(set(payload.rule_ids)):
        raise HTTPException(
            status_code=422, detail="部分自动化规则不存在或不属于当前家庭"
        )
    config = {
        "timezone": payload.timezone,
        "time": payload.time,
        "weekdays": payload.weekdays,
        "frequency": payload.frequency,
        "interval": payload.interval,
    }
    for rule in rules:
        rule.trigger_type = "schedule"
        rule.triggers = []
        rule.triggers.append(
            AutomationTrigger(type="schedule", config_json=json.dumps(config))
        )
        rule.version += 1
    db.commit()
    return ApiResponse.ok(BatchEnableRead(updated_count=len(rules), unchanged_count=0))
