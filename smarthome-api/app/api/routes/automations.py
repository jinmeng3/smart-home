from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import (
    CURRENT_USER_DEPENDENCY,
    DB_DEPENDENCY,
    HOUSEHOLD_MEMBER_DEPENDENCY,
)
from app.models.automation import Automation
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
    batch_enable_service,
    batch_schedule_automations_service,
    create_automation_service,
    execute_automation_service,
    get_automation,
    list_automations_service,
    list_executions_service,
    serialize,
    update_automation_service,
)

router = APIRouter(tags=["automations"])


def accessible_automation(
    db: Session, user: User, automation_id: int
) -> tuple[Automation, int]:
    """校验自动化规则归属当前用户所在家庭，返回规则对象及家庭ID。"""
    household_id = db.scalar(
        select(HouseholdMembership.household_id)
        .join(Automation, Automation.household_id == HouseholdMembership.household_id)
        .where(HouseholdMembership.user_id == user.id, Automation.id == automation_id)
    )
    if household_id is None:
        raise HTTPException(status_code=404, detail="自动化规则不存在")
    return get_automation(db, automation_id, household_id), household_id


# === 自动化规则 ===


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
    """分页查询家庭自动化规则，支持关键字、触发类型和启用状态筛选。"""
    return ApiResponse.ok(
        list_automations_service(
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
    """在当前家庭下创建自动化规则。"""
    return ApiResponse.ok(
        create_automation_service(db, household_id, user.id, payload), "created"
    )


@router.get("/automations/{automation_id}", response_model=ApiResponse[AutomationRead])
def read_automation(
    automation_id: int,
    db: Session = DB_DEPENDENCY,
    user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[AutomationRead]:
    """读取单个自动化规则详情。"""
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
    """更新自动化规则配置。"""
    _, household_id = accessible_automation(db, user, automation_id)
    return ApiResponse.ok(update_automation_service(db, automation_id, household_id, payload))


# === 自动化执行 ===


@router.patch(
    "/automations/{automation_id}/enabled", response_model=ApiResponse[EnabledRead]
)
def change_automation_enabled(
    automation_id: int,
    payload: EnabledWrite,
    db: Session = DB_DEPENDENCY,
    user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[EnabledRead]:
    """启用或停用自动化规则。"""
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
    """手动触发执行自动化规则，支持幂等键防止重复执行。"""
    automation, _ = accessible_automation(db, user, automation_id)
    return ApiResponse.ok(
        execute_automation_service(db, automation, payload.source, idempotency_key)
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
    """分页查询自动化规则的执行记录。"""
    automation, _ = accessible_automation(db, user, automation_id)
    return ApiResponse.ok(
        list_executions_service(db, automation, page, page_size, status_filter)
    )


# === 批量操作 ===


@router.post("/automations/batch-enable", response_model=ApiResponse[BatchEnableRead])
def batch_enable_automations(
    payload: BatchEnableWrite,
    db: Session = DB_DEPENDENCY,
    user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[BatchEnableRead]:
    """批量启用或停用自动化规则。"""
    household_id = db.scalar(
        select(HouseholdMembership.household_id)
        .where(HouseholdMembership.user_id == user.id)
        .order_by(HouseholdMembership.id)
    )
    if household_id is None:
        raise HTTPException(status_code=403, detail="当前用户尚未加入家庭")
    return ApiResponse.ok(batch_enable_service(db, household_id, payload))


@router.put("/automations/schedules/batch", response_model=ApiResponse[BatchEnableRead])
def batch_set_schedule(
    payload: BatchScheduleWrite,
    db: Session = DB_DEPENDENCY,
    user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[BatchEnableRead]:
    """批量设置自动化规则的定时触发配置。"""
    household_id = db.scalar(
        select(HouseholdMembership.household_id)
        .where(HouseholdMembership.user_id == user.id)
        .order_by(HouseholdMembership.id)
    )
    if household_id is None:
        raise HTTPException(status_code=403, detail="当前用户尚未加入家庭")
    return ApiResponse.ok(batch_schedule_automations_service(db, household_id, payload))
