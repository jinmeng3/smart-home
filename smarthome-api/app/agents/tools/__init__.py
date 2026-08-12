from app.agents.context import AgentContext
from app.agents.tools.base import build_query_tool
from app.agents.tools.query import automations, devices, executions, rooms, scenes
from sqlalchemy.orm import Session


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
    ]
