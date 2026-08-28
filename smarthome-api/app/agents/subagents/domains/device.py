from app.agents.context import AgentContext
from app.agents.subagents.factory import build_subagent
from langchain_core.language_models import BaseChatModel
from sqlalchemy.orm import Session

DEVICE_SYSTEM_PROMPT = """你是智能家居设备管家，负责查询当前家庭的设备与房间状态。

约束：
- 只通过工具读取数据，不臆测设备状态；
- 所有查询只访问当前家庭 household_id 的数据；
- 不执行任何写操作，不创建场景或自动化。
"""


def build_device_subagent(context: AgentContext, db: Session, model: BaseChatModel):
    """构建 device 只读子 Agent。"""
    return build_subagent("device", context, db, model)
