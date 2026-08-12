from app.agents.context import AgentContext
from app.agents.tools.base import build_query_tool
from app.agents.tools.query.devices import (
    GetDeviceInput,
    ListDevicesInput,
    _get_device,
    _list_devices,
)
from langchain_core.tools import BaseTool
from sqlalchemy.orm import Session


def get_household_tools(context: AgentContext, db: Session) -> list[BaseTool]:
    return [
        build_query_tool(
            "list_devices",
            "列出当前家庭的设备，可按房间、设备类型和状态筛选",
            ListDevicesInput,
            context,
            db,
            _list_devices,
        ),
        build_query_tool(
            "get_device",
            "按设备 ID 获取当前家庭内的设备详情、状态、连接方式、固件和最近日志",
            GetDeviceInput,
            context,
            db,
            _get_device,
        ),
    ]
