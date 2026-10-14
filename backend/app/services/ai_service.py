from app.common.exceptions import BusinessException
from app.schemas.ai import ChatRequest, ChatResponse
from app.services.llm_client import llm_client


SYSTEM_PROMPT = """你是智能实验室预约系统的助手，请用简洁、准确、友好的中文回答。
你可以介绍本系统的预约流程：登录后打开实验室列表，选择实验室或设备，填写日期和时段后提交，预约状态为待审核；管理员审核通过后方可使用；本人只能取消待审核预约。
你目前不能查询真实实验室、设备或预约数据。用户询问具体实验室开放时间、设备库存、维修状态或预约占用情况时，请说明当前无法查询实时数据，并引导用户查看系统页面。
不要编造具体实验室、设备或预约数据。与实验室预约无关的问题可以简短说明你的服务范围。"""


async def chat(data: ChatRequest) -> ChatResponse:
    history = [message.model_dump() for message in data.messages]
    if not history or not history[-1]["content"].strip():
        raise BusinessException(message="请输入您要对话的内容", code=400)

    answer = await llm_client.chat(
        [{"role": "system", "content": SYSTEM_PROMPT}, *history]
    )
    if not answer.strip():
        raise BusinessException(message="大模型返回了空内容，请重试", code=502)
    return ChatResponse(content=answer)
