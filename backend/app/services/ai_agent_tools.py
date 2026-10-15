"""Tools exposed to the LangGraph laboratory assistant."""

import asyncio
import json
import logging
from datetime import date
from typing import Any
from uuid import uuid4

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.database import SessionLocal
from app.schemas.reservation import ReservationCreateRequest
from app.services import reservation_service
from app.services.ai_tools import create_read_only_tools

logger = logging.getLogger(__name__)


class _ToolArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _PrepareReservationArgs(_ToolArgs):
    lab_id: int = Field(gt=0, description="目标实验室的数据库 ID。")
    equipment_id: int | None = Field(
        default=None, gt=0, description="预约设备时填写设备数据库 ID；预约实验室时省略。"
    )
    date: str = Field(
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="预约日期，格式 YYYY-MM-DD。",
    )
    start_time: str = Field(
        pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$",
        description="开始时间，24 小时制 HH:mm。",
    )
    end_time: str = Field(
        pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$",
        description="结束时间，24 小时制 HH:mm。",
    )
    remark: str | None = Field(default=None, max_length=255, description="预约用途或备注。")


def _json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _prepare_reservation_sync(arguments: dict[str, Any]) -> str:
    db: Session = SessionLocal()
    try:
        request = ReservationCreateRequest.model_validate(arguments)
        lab, equipment = reservation_service.validate_reservation(db, request)
        return _json(
            {
                "ok": True,
                "draft_id": str(uuid4()),
                "draft": {
                    "lab_id": lab.id,
                    "lab_name": lab.name,
                    "location": lab.location,
                    "equipment_id": equipment.id if equipment else None,
                    "equipment_name": equipment.name if equipment else None,
                    "date": request.date,
                    "start_time": request.start_time,
                    "end_time": request.end_time,
                    "remark": request.remark,
                },
            }
        )
    except BusinessException as exc:
        return _json({"ok": False, "error": exc.message})
    except Exception:
        logger.exception("AI reservation proposal validation failed")
        return _json({"ok": False, "error": "预约信息校验暂不可用，请稍后重试。"})
    finally:
        db.close()


async def _prepare_reservation(**arguments: Any) -> str:
    return await asyncio.to_thread(_prepare_reservation_sync, arguments)


async def _get_today() -> str:
    return _json({"date": date.today().isoformat()})


def create_agent_tools(*, include_reservation_proposal: bool) -> list[StructuredTool]:
    """Create read tools and, when enabled, a non-writing reservation proposal tool."""
    tools = create_read_only_tools()
    tools.append(
        StructuredTool.from_function(
            coroutine=_get_today,
            name="get_today",
            description="获取服务器本地当前日期；处理预约日期时先调用此工具核对今天。",
            args_schema=_ToolArgs,
        )
    )
    if include_reservation_proposal:
        tools.append(
            StructuredTool.from_function(
                coroutine=_prepare_reservation,
                name="prepare_reservation",
                description=(
                    "根据用户明确提出的预约意图，核对预约字段、实验室开放时段、设备归属和已有冲突，"
                    "只生成待确认草案，不会写数据库。必须在拿到用户明确确认后，"
                    "由后端工作流提交预约；不要把草案描述成已经提交。"
                ),
                args_schema=_PrepareReservationArgs,
            )
        )
    return tools
