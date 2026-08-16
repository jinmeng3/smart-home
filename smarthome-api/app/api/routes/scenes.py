from fastapi import APIRouter, Query, status
from sqlalchemy.orm import Session

from app.api.deps import (
    CURRENT_USER_DEPENDENCY,
    DB_DEPENDENCY,
    DEFAULT_HOUSEHOLD_DEPENDENCY,
)
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.scene import (
    SceneBatchEnabledResult,
    SceneBatchEnabledWrite,
    SceneBatchScheduleResult,
    SceneBatchScheduleWrite,
    SceneCopyWrite,
    SceneDraftRead,
    SceneDraftWrite,
    SceneEnabledRead,
    SceneEnabledWrite,
    SceneExecuteWrite,
    SceneExecutionRead,
    SceneListRead,
    SceneLogListRead,
    SceneOrderRead,
    SceneOrderWrite,
    ScenePreviewRead,
    ScenePreviewWrite,
    SceneRead,
    SceneSummaryRead,
    SceneTemplateListRead,
    SceneTemplatePreviewRead,
    SceneTemplateUseWrite,
    SceneWrite,
)
from app.services.scene import (
    add_draft_service,
    add_scene_service,
    batch_change_enabled_service,
    batch_set_schedule_service,
    change_enabled_service,
    duplicate_scene_service,
    edit_scene_service,
    get_execution_service,
    get_logs_service,
    get_scene_preview_service,
    get_scenes_service,
    get_summary_service,
    get_template_preview_service,
    get_templates_service,
    import_template_service,
    remove_scene_service,
    reorder_scenes_service,
    run_scene_service,
)

router = APIRouter(prefix="/scenes", tags=["scenes"])
KEYWORD_QUERY = Query(default=None, max_length=100)
TRIGGER_QUERY = Query(default=None, pattern="^(manual|schedule|location|device)$")
ENABLED_QUERY = Query(default="all", pattern="^(all|enabled|disabled)$")
LIMIT_QUERY = Query(default=20, ge=1, le=100)
CATEGORY_QUERY = Query(default=None, max_length=40)


# === 场景管理 ===


@router.get("", response_model=ApiResponse[SceneListRead])
def get_scenes(
    keyword: str | None = KEYWORD_QUERY,
    trigger_type: str | None = TRIGGER_QUERY,
    enabled: str = ENABLED_QUERY,
    db: Session = DB_DEPENDENCY,
    household_id: int = DEFAULT_HOUSEHOLD_DEPENDENCY,
) -> ApiResponse[SceneListRead]:
    """筛选并返回按自定义顺序排列的场景。"""
    return ApiResponse(
        data=get_scenes_service(db, household_id, keyword, trigger_type, enabled)
    )


@router.post(
    "", response_model=ApiResponse[SceneRead], status_code=status.HTTP_201_CREATED
)
def add_scene(
    payload: SceneWrite,
    db: Session = DB_DEPENDENCY,
    household_id: int = DEFAULT_HOUSEHOLD_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[SceneRead]:
    """创建场景及其执行步骤。"""
    return ApiResponse(
        data=add_scene_service(db, household_id, current_user.id, payload),
        message="created",
    )


@router.get("/summary", response_model=ApiResponse[SceneSummaryRead])
def get_summary(
    db: Session = DB_DEPENDENCY,
    household_id: int = DEFAULT_HOUSEHOLD_DEPENDENCY,
) -> ApiResponse[SceneSummaryRead]:
    """返回场景数量与本月执行统计。"""
    return ApiResponse(data=get_summary_service(db, household_id))


@router.patch("/order", response_model=ApiResponse[SceneOrderRead])
def reorder_scenes(
    payload: SceneOrderWrite,
    db: Session = DB_DEPENDENCY,
    household_id: int = DEFAULT_HOUSEHOLD_DEPENDENCY,
) -> ApiResponse[SceneOrderRead]:
    """在单个事务中批量更新场景顺序。"""
    return ApiResponse(data=reorder_scenes_service(db, household_id, payload))


@router.post(
    "/drafts",
    response_model=ApiResponse[SceneDraftRead],
    status_code=status.HTTP_201_CREATED,
)
def add_draft(
    payload: SceneDraftWrite,
    db: Session = DB_DEPENDENCY,
    household_id: int = DEFAULT_HOUSEHOLD_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[SceneDraftRead]:
    """保存尚未发布的场景表单快照。"""
    return ApiResponse(
        data=add_draft_service(db, household_id, current_user.id, payload),
        message="created",
    )


@router.get("/templates", response_model=ApiResponse[SceneTemplateListRead])
def get_templates(
    keyword: str | None = KEYWORD_QUERY,
    category: str | None = CATEGORY_QUERY,
    limit: int = LIMIT_QUERY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[SceneTemplateListRead]:
    """按关键字、分类读取可用模板。"""
    return ApiResponse(data=get_templates_service(db, keyword, category, limit))


@router.get(
    "/templates/{template_id}/preview",
    response_model=ApiResponse[SceneTemplatePreviewRead],
)
def get_template_preview(
    template_id: str,
    db: Session = DB_DEPENDENCY,
    household_id: int = DEFAULT_HOUSEHOLD_DEPENDENCY,
) -> ApiResponse[SceneTemplatePreviewRead]:
    """预览模板步骤及本地设备匹配情况。"""
    return ApiResponse(data=get_template_preview_service(db, household_id, template_id))


@router.post("/templates/{template_id}/use", response_model=ApiResponse[SceneRead])
def import_template(
    template_id: str,
    payload: SceneTemplateUseWrite,
    db: Session = DB_DEPENDENCY,
    household_id: int = DEFAULT_HOUSEHOLD_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[SceneRead]:
    """复制模板数据并创建可编辑场景。"""
    return ApiResponse(
        data=import_template_service(
            db, household_id, current_user.id, template_id, payload
        ),
        message="created",
    )


# === 场景执行 ===


@router.get(
    "/executions/{execution_id}", response_model=ApiResponse[SceneExecutionRead]
)
def get_execution(
    execution_id: str,
    db: Session = DB_DEPENDENCY,
    household_id: int = DEFAULT_HOUSEHOLD_DEPENDENCY,
) -> ApiResponse[SceneExecutionRead]:
    """返回执行过程及逐步状态，供前端轮询。"""
    return ApiResponse(data=get_execution_service(db, household_id, execution_id))


@router.put("/{scene_id}", response_model=ApiResponse[SceneRead])
def edit_scene(
    scene_id: str,
    payload: SceneWrite,
    db: Session = DB_DEPENDENCY,
    household_id: int = DEFAULT_HOUSEHOLD_DEPENDENCY,
) -> ApiResponse[SceneRead]:
    """覆盖场景信息及步骤。"""
    return ApiResponse(data=edit_scene_service(db, household_id, scene_id, payload))


@router.delete("/{scene_id}", response_model=ApiResponse[None])
def remove_scene(
    scene_id: str,
    db: Session = DB_DEPENDENCY,
    household_id: int = DEFAULT_HOUSEHOLD_DEPENDENCY,
) -> ApiResponse[None]:
    """删除场景及其执行步骤、执行日志。"""
    remove_scene_service(db, household_id, scene_id)
    return ApiResponse(message="deleted")


@router.patch("/{scene_id}/enabled", response_model=ApiResponse[SceneEnabledRead])
def change_enabled(
    scene_id: str,
    payload: SceneEnabledWrite,
    db: Session = DB_DEPENDENCY,
    household_id: int = DEFAULT_HOUSEHOLD_DEPENDENCY,
) -> ApiResponse[SceneEnabledRead]:
    """启用或停用场景。"""
    scene = change_enabled_service(db, household_id, scene_id, payload.enabled)
    return ApiResponse(
        data=SceneEnabledRead.model_validate(scene, from_attributes=True)
    )


@router.post("/{scene_id}/execute", response_model=ApiResponse[SceneExecutionRead])
def run_scene(
    scene_id: str,
    payload: SceneExecuteWrite,
    db: Session = DB_DEPENDENCY,
    household_id: int = DEFAULT_HOUSEHOLD_DEPENDENCY,
) -> ApiResponse[SceneExecutionRead]:
    """校验风险并记录完整执行结果。"""
    return ApiResponse(
        data=run_scene_service(
            db, household_id, scene_id, payload.confirm_high_risk, payload.source
        )
    )


@router.post("/{scene_id}/copy", response_model=ApiResponse[SceneRead])
def duplicate_scene(
    scene_id: str,
    payload: SceneCopyWrite,
    db: Session = DB_DEPENDENCY,
    household_id: int = DEFAULT_HOUSEHOLD_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[SceneRead]:
    """复制场景及全部步骤。"""
    return ApiResponse(
        data=duplicate_scene_service(
            db, household_id, current_user.id, scene_id, payload.name
        ),
        message="created",
    )


@router.get("/{scene_id}/logs", response_model=ApiResponse[SceneLogListRead])
def get_logs(
    scene_id: str,
    limit: int = LIMIT_QUERY,
    db: Session = DB_DEPENDENCY,
    household_id: int = DEFAULT_HOUSEHOLD_DEPENDENCY,
) -> ApiResponse[SceneLogListRead]:
    """读取场景最近执行日志。"""
    return ApiResponse(data=get_logs_service(db, household_id, scene_id, limit))


@router.post("/{scene_id}/preview", response_model=ApiResponse[ScenePreviewRead])
def get_scene_preview(
    scene_id: str,
    _payload: ScenePreviewWrite,
    db: Session = DB_DEPENDENCY,
    household_id: int = DEFAULT_HOUSEHOLD_DEPENDENCY,
) -> ApiResponse[ScenePreviewRead]:
    """返回动作链，不实际控制设备。"""
    return ApiResponse(data=get_scene_preview_service(db, household_id, scene_id))


# === 批量操作 ===


@router.post("/batch/enabled", response_model=ApiResponse[SceneBatchEnabledResult])
def batch_change_enabled(
    payload: SceneBatchEnabledWrite,
    db: Session = DB_DEPENDENCY,
    household_id: int = DEFAULT_HOUSEHOLD_DEPENDENCY,
) -> ApiResponse[SceneBatchEnabledResult]:
    """批量启用或停用场景。"""
    return ApiResponse(data=batch_change_enabled_service(db, household_id, payload))


@router.post("/batch/schedule", response_model=ApiResponse[SceneBatchScheduleResult])
def batch_set_schedule(
    payload: SceneBatchScheduleWrite,
    db: Session = DB_DEPENDENCY,
    household_id: int = DEFAULT_HOUSEHOLD_DEPENDENCY,
) -> ApiResponse[SceneBatchScheduleResult]:
    """批量设置场景的触发类型和定时描述。"""
    return ApiResponse(data=batch_set_schedule_service(db, household_id, payload))
