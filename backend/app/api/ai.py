from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_current_admin, get_current_user
from app.models.user import User
from app.schemas.ai import ChatRequest, KnowledgeIndexResponse
from app.services import ai_service, kb_service

router = APIRouter(prefix="/ai", tags=["AI 对话"])


@router.post("/chat")
async def chat(
    request: Request,
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    graph = getattr(request.app.state, "ai_graph", None)
    if graph is None:
        raise BusinessException(message="AI 助手当前未启用", code=503)
    result = await ai_service.chat(graph, current_user, data)
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
