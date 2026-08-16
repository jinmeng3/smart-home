from app.agents.context import AgentContext
from app.agents.tools.base import build_query_tool
from app.agents.tools.execute import automations as execute_automations
from app.agents.tools.execute import scenes as execute_scenes
from app.agents.tools.preview import automations as preview_automations
from app.agents.tools.preview import scenes as preview_scenes
from app.agents.tools.query import automations, devices, executions, rooms, scenes
from sqlalchemy.orm import Session

WRITE_TOOL_NAMES = {
    "execute_scene",
    "create_automation",
    "update_automation",
    "set_automation_enabled",
    "delete_automation",
}


def get_household_tools(context: AgentContext, db: Session):
    return [
        build_query_tool(
            "list_rooms",
            "列出当前家庭的全部房间，可按楼层(floor)或房间类型(room_type)筛选；返回房间id、名称、楼层、类型、面积、舒适度和设备数量",
            rooms.ListRoomsInput,
            context,
            db,
            rooms.list_rooms,
        ),
        build_query_tool(
            "get_room",
            "获取指定房间详情及其设备列表；通过room_id或room_name指定，至少提供一个",
            rooms.GetRoomInput,
            context,
            db,
            rooms.get_room,
        ),
        build_query_tool(
            "list_devices",
            "列出当前家庭的设备，可按房间(room)、类型(device_type如light/air_conditioner)、状态(status如online/offline/warning/running)筛选",
            devices.ListDevicesInput,
            context,
            db,
            devices.list_devices,
        ),
        build_query_tool(
            "get_device",
            "获取指定设备详情（状态、连接方式、固件、最后在线时间）；通过device_id或name指定，至少提供一个",
            devices.GetDeviceInput,
            context,
            db,
            devices.get_device,
        ),
        build_query_tool(
            "list_scenes",
            "列出当前家庭的场景，可按关键词(keyword)、启用状态(enabled: enabled/disabled)、触发类型(trigger_type)筛选",
            scenes.ListScenesInput,
            context,
            db,
            scenes.list_scenes,
        ),
        build_query_tool(
            "get_scene",
            "获取指定场景详情及其步骤；通过scene_id或name指定，至少提供一个",
            scenes.GetSceneInput,
            context,
            db,
            scenes.get_scene,
        ),
        build_query_tool(
            "list_automations",
            "列出当前家庭的自动化规则，可按关键词(keyword)、触发类型(trigger_type)、启用状态(enabled)筛选",
            automations.ListAutomationsInput,
            context,
            db,
            automations.list_automations,
        ),
        build_query_tool(
            "get_automation",
            "获取指定自动化规则详情（触发器、条件、动作）；通过automation_id或name指定，至少提供一个",
            automations.GetAutomationInput,
            context,
            db,
            automations.get_automation,
        ),
        build_query_tool(
            "list_device_logs",
            "查询当前家庭的设备日志，可按整数 device_id 过滤",
            executions.ListDeviceLogsInput,
            context,
            db,
            executions.list_device_logs,
        ),
        build_query_tool(
            "list_scene_executions",
            "查询当前家庭的场景执行记录，可按字符串 scene_id 过滤",
            executions.ListSceneExecutionsInput,
            context,
            db,
            executions.list_scene_executions,
        ),
        build_query_tool(
            "list_automation_executions",
            "查询当前家庭的自动化执行记录，可按整数 automation_id 过滤",
            executions.ListAutomationExecutionsInput,
            context,
            db,
            executions.list_automation_executions,
        ),
        # 只读预览工具
        build_query_tool(
            "preview_scene",
            "预览指定场景的执行步骤、影响设备和风险等级，不会实际执行场景",
            preview_scenes.PreviewSceneInput,
            context,
            db,
            preview_scenes.preview_scene,
        ),
        build_query_tool(
            "preview_automation_change",
            "预览自动化规则的变更内容，对比当前配置与变更后的差异，不会实际修改任何数据",
            preview_automations.PreviewAutomationChangeInput,
            context,
            db,
            preview_automations.preview_automation_change,
        ),
        build_query_tool(
            "detect_automation_conflicts",
            "检测自动化规则之间的时间重叠、设备冲突和循环触发风险，不会实际修改任何数据",
            preview_automations.DetectAutomationConflictsInput,
            context,
            db,
            preview_automations.detect_automation_conflicts,
        ),
        # 写工具（注册但实际执行由受控写操作节点完成）
        build_query_tool(
            "execute_scene",
            (
                "请求执行当前家庭中的场景。该操作可能需要用户确认。"
                "只能传入scene_id，不得传入household_id、风险等级或确认状态"
            ),
            execute_scenes.ExecuteSceneInput,
            context,
            db,
            lambda **_: {
                "ok": False,
                "error": "execute_scene只能由受控写操作节点执行",
            },
        ),
        build_query_tool(
            "create_automation",
            (
                "在当前家庭中创建自动化规则，包含触发器、条件和动作。"
                "该操作可能需要用户确认。"
            ),
            execute_automations.CreateAutomationInput,
            context,
            db,
            lambda **_: {
                "ok": False,
                "error": "create_automation只能由受控写操作节点执行",
            },
        ),
        build_query_tool(
            "update_automation",
            (
                "更新当前家庭中的自动化规则。需携带version参数实现乐观锁。"
                "该操作可能需要用户确认。"
            ),
            execute_automations.UpdateAutomationInput,
            context,
            db,
            lambda **_: {
                "ok": False,
                "error": "update_automation只能由受控写操作节点执行",
            },
        ),
        build_query_tool(
            "set_automation_enabled",
            (
                "启用或停用当前家庭中的自动化规则。"
                "该操作可能需要用户确认。"
            ),
            execute_automations.SetAutomationEnabledInput,
            context,
            db,
            lambda **_: {
                "ok": False,
                "error": "set_automation_enabled只能由受控写操作节点执行",
            },
        ),
        build_query_tool(
            "delete_automation",
            (
                "删除当前家庭中的自动化规则。"
                "该操作需要用户确认。"
            ),
            execute_automations.DeleteAutomationInput,
            context,
            db,
            lambda **_: {
                "ok": False,
                "error": "delete_automation只能由受控写操作节点执行",
            },
        ),
    ]