from fastapi import APIRouter, Query, status
from sqlalchemy.orm import Session

from app.api.deps import CURRENT_USER_DEPENDENCY, DB_DEPENDENCY
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
    batch_set_scene_enabled,
    batch_set_scene_schedule,
    copy_scene,
    create_scene,
    delete_scene,
    execute_scene,
    list_scene_logs,
    list_scenes,
    list_templates,
    preview_scene,
    preview_template,
    read_execution,
    save_draft,
    set_scene_enabled,
    summarize_scenes,
    update_scene,
    update_scene_order,
    use_template,
)

router = APIRouter(prefix="/scenes", tags=["scenes"], dependencies=[CURRENT_USER_DEPENDENCY])
KEYWORD_QUERY = Query(default=None, max_length=100)
TRIGGER_QUERY = Query(default=None, pattern="^(manual|schedule|location|device)$")
ENABLED_QUERY = Query(default="all", pattern="^(all|enabled|disabled)$")
LIMIT_QUERY = Query(default=20, ge=1, le=100)
CATEGORY_QUERY = Query(default=None, max_length=40)


@router.get("", response_model=ApiResponse[SceneListRead])
def get_scenes(
    keyword: str | None = KEYWORD_QUERY,
    trigger_type: str | None = TRIGGER_QUERY,
    enabled: str = ENABLED_QUERY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[SceneListRead]:
    """筛选并返回按自定义顺序排列的场景。"""
    return ApiResponse(data=list_scenes(db, keyword, trigger_type, enabled))


@router.post(
    "", response_model=ApiResponse[SceneRead], status_code=status.HTTP_201_CREATED
)
def add_scene(
    payload: SceneWrite, db: Session = DB_DEPENDENCY
) -> ApiResponse[SceneRead]:
    """创建场景及其执行步骤。"""
    return ApiResponse(data=create_scene(db, payload), message="created")


@router.get("/summary", response_model=ApiResponse[SceneSummaryRead])
def get_summary(db: Session = DB_DEPENDENCY) -> ApiResponse[SceneSummaryRead]:
    """返回场景数量与本月执行统计。"""
    return ApiResponse(data=summarize_scenes(db))


@router.patch("/order", response_model=ApiResponse[SceneOrderRead])
def reorder_scenes(
    payload: SceneOrderWrite, db: Session = DB_DEPENDENCY
) -> ApiResponse[SceneOrderRead]:
    """在单个事务中批量更新场景顺序。"""
    return ApiResponse(data=update_scene_order(db, payload))


@router.post(
    "/drafts",
    response_model=ApiResponse[SceneDraftRead],
    status_code=status.HTTP_201_CREATED,
)
def add_draft(
    payload: SceneDraftWrite, db: Session = DB_DEPENDENCY
) -> ApiResponse[SceneDraftRead]:
    """保存尚未发布的场景表单快照。"""
    return ApiResponse(data=save_draft(db, payload), message="created")


@router.get("/templates", response_model=ApiResponse[SceneTemplateListRead])
def get_templates(
    keyword: str | None = KEYWORD_QUERY,
    category: str | None = CATEGORY_QUERY,
    limit: int = LIMIT_QUERY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[SceneTemplateListRead]:
    """按关键字、分类读取可用模板。"""
    return ApiResponse(data=list_templates(db, keyword, category, limit))


@router.get(
    "/templates/{template_id}/preview",
    response_model=ApiResponse[SceneTemplatePreviewRead],
)
def get_template_preview(
    template_id: str, db: Session = DB_DEPENDENCY
) -> ApiResponse[SceneTemplatePreviewRead]:
    """预览模板步骤及本地设备匹配情况。"""
    return ApiResponse(data=preview_template(db, template_id))


@router.post("/templates/{template_id}/use", response_model=ApiResponse[SceneRead])
def import_template(
    template_id: str,
    payload: SceneTemplateUseWrite,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[SceneRead]:
    """复制模板数据并创建可编辑场景。"""
    return ApiResponse(data=use_template(db, template_id, payload), message="created")


@router.get(
    "/executions/{execution_id}", response_model=ApiResponse[SceneExecutionRead]
)
def get_execution(
    execution_id: str, db: Session = DB_DEPENDENCY
) -> ApiResponse[SceneExecutionRead]:
    """返回执行过程及逐步状态，供前端轮询。"""
    return ApiResponse(data=read_execution(db, execution_id))


@router.put("/{scene_id}", response_model=ApiResponse[SceneRead])
def edit_scene(
    scene_id: str, payload: SceneWrite, db: Session = DB_DEPENDENCY
) -> ApiResponse[SceneRead]:
    """覆盖场景信息及步骤。"""
    return ApiResponse(data=update_scene(db, scene_id, payload))


@router.delete("/{scene_id}", response_model=ApiResponse[None])
def remove_scene(scene_id: str, db: Session = DB_DEPENDENCY) -> ApiResponse[None]:
    """删除场景及其执行步骤、执行日志。"""
    delete_scene(db, scene_id)
    return ApiResponse(message="deleted")


@router.patch("/{scene_id}/enabled", response_model=ApiResponse[SceneEnabledRead])
def change_enabled(
    scene_id: str,
    payload: SceneEnabledWrite,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[SceneEnabledRead]:
    """启用或停用场景。"""
    scene = set_scene_enabled(db, scene_id, payload.enabled)
    return ApiResponse(
        data=SceneEnabledRead.model_validate(scene, from_attributes=True)
    )


@router.post("/{scene_id}/execute", response_model=ApiResponse[SceneExecutionRead])
def run_scene(
    scene_id: str,
    payload: SceneExecuteWrite,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[SceneExecutionRead]:
    """校验风险并记录完整执行结果。"""
    return ApiResponse(
        data=execute_scene(db, scene_id, payload.confirm_high_risk, payload.source)
    )


@router.post("/{scene_id}/copy", response_model=ApiResponse[SceneRead])
def duplicate_scene(
    scene_id: str, payload: SceneCopyWrite, db: Session = DB_DEPENDENCY
) -> ApiResponse[SceneRead]:
    """复制场景及全部步骤。"""
    return ApiResponse(data=copy_scene(db, scene_id, payload.name), message="created")


@router.get("/{scene_id}/logs", response_model=ApiResponse[SceneLogListRead])
def get_logs(
    scene_id: str, limit: int = LIMIT_QUERY, db: Session = DB_DEPENDENCY
) -> ApiResponse[SceneLogListRead]:
    """读取场景最近执行日志。"""
    return ApiResponse(data=list_scene_logs(db, scene_id, limit))


@router.post("/{scene_id}/preview", response_model=ApiResponse[ScenePreviewRead])
def get_scene_preview(
    scene_id: str,
    _payload: ScenePreviewWrite,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[ScenePreviewRead]:
    """返回动作链，不实际控制设备。"""
    return ApiResponse(data=preview_scene(db, scene_id))


@router.post("/batch/enabled", response_model=ApiResponse[SceneBatchEnabledResult])
def batch_change_enabled(
    payload: SceneBatchEnabledWrite, db: Session = DB_DEPENDENCY
) -> ApiResponse[SceneBatchEnabledResult]:
    """批量启用或停用场景。"""
    return ApiResponse(data=batch_set_scene_enabled(db, payload))


@router.post("/batch/schedule", response_model=ApiResponse[SceneBatchScheduleResult])
def batch_set_schedule(
    payload: SceneBatchScheduleWrite, db: Session = DB_DEPENDENCY
) -> ApiResponse[SceneBatchScheduleResult]:
    """批量设置场景的触发类型和定时描述。"""
    return ApiResponse(data=batch_set_scene_schedule(db, payload))
