from app.agents.context import AgentContext
from app.agents.tools.query.devices import ListDevicesInput, _list_devices
from langchain_core.tools import tool
from sqlalchemy.orm import Session


def get_household_tools(context: AgentContext, db: Session):

    return [
        tool("list_devices", description="列出设备", args_schema=ListDevicesInput)(
            lambda **kw: _list_devices(db, context, **kw)
        ),
    ]
