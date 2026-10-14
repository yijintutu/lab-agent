from fastapi import APIRouter, Depends

from app.common.response import Response
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.ai import ChatRequest
from app.services import ai_service

router = APIRouter(prefix="/ai", tags=["AI 对话"])


@router.post("/chat")
async def chat(
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    # current_user 由 JWT 注入；阶段②不持久化会话，也不接受客户端提供身份字段。
    _ = current_user.id
    result = await ai_service.chat(data)
    return Response.success(data=result)
