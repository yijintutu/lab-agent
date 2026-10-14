from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_current_admin, get_current_user
from app.models.user import User
from app.schemas.ai import ChatRequest, KnowledgeIndexResponse
from app.services import ai_service, kb_service

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


@router.post("/kb/rebuild")
def rebuild_knowledge_index(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """从 Markdown 规则文件和数据库静态资料重建向量索引（管理员）。"""
    _ = current_admin.id
    result = KnowledgeIndexResponse.model_validate(kb_service.rebuild(db))
    return Response.success(message="知识库索引已重建", data=result)
