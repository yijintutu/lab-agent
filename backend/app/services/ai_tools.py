"""Read-only LangChain tools backed by existing business services."""

import asyncio
import json
import logging
from collections.abc import Callable
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.database import SessionLocal
from app.services import equipment_service, lab_service

logger = logging.getLogger(__name__)

MAX_TOOL_PAGE_SIZE = 20
MAX_TOOL_TEXT_LENGTH = 500


class _ToolArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _ListOpenLabsArgs(_ToolArgs):
    keywords: str | None = Field(
        default=None,
        max_length=50,
        description="实验室名称关键字；不筛选时省略或传空字符串。",
    )


class _ListLabEquipmentsArgs(_ToolArgs):
    lab_id: int = Field(gt=0, description="目标实验室的数据库 ID，必须是正整数。")
    keywords: str | None = Field(
        default=None,
        max_length=50,
        description="设备名称关键字；不筛选时省略或传空字符串。",
    )


def _trimmed(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip()[:50] or None


def _short_text(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)[:MAX_TOOL_TEXT_LENGTH]


def _json_result(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _run_read_query(query: Callable[[Session], dict[str, Any]]) -> str:
    """Create and close a tool-owned session in the worker that runs the query."""
    db = SessionLocal()
    try:
        return _json_result(query(db))
    except BusinessException as exc:
        return _json_result({"error": exc.message})
    except Exception:
        logger.exception("AI read-only tool query failed")
        return _json_result({"error": "实时数据查询暂不可用，请稍后重试。"})
    finally:
        db.close()


def _query_open_labs(db: Session, keywords: str | None) -> dict[str, Any]:
    page = lab_service.get_lab_page_list(
        db,
        page=1,
        page_size=MAX_TOOL_PAGE_SIZE,
        keywords=_trimmed(keywords),
        status=1,
    )
    labs = [
        {
            "id": item.id,
            "name": item.name,
            "location": item.location,
            "capacity": item.capacity,
            "open_time": item.open_time,
            "close_time": item.close_time,
            "status": item.status,
        }
        for item in page.list
    ]
    return {
        "total": page.total,
        "returned": len(labs),
        "truncated": page.total > len(labs),
        "labs": labs,
    }


def _query_lab_equipments(
    db: Session, lab_id: int, keywords: str | None
) -> dict[str, Any]:
    lab = lab_service.get_lab(db, lab_id)
    page = equipment_service.get_equipment_page_list(
        db,
        page=1,
        page_size=MAX_TOOL_PAGE_SIZE,
        keywords=_trimmed(keywords),
        lab_id=lab_id,
    )
    equipments = [
        {
            "id": item.id,
            "lab_id": item.lab_id,
            "lab_name": _short_text(item.lab_name),
            "name": _short_text(item.name),
            "description": _short_text(item.description),
            "spec": _short_text(item.spec),
            "status": item.status,
            "status_label": {0: "维修中", 1: "正常"}.get(item.status, "未知"),
        }
        for item in page.list
    ]
    return {
        "lab": {"id": lab.id, "name": _short_text(lab.name)},
        "total": page.total,
        "returned": len(equipments),
        "truncated": page.total > len(equipments),
        "equipments": equipments,
    }


def create_read_only_tools() -> list[StructuredTool]:
    """Build the allowlisted tools available to an authenticated chat request."""

    async def list_open_labs(keywords: str | None = None) -> str:
        return await asyncio.to_thread(
            _run_read_query, lambda db: _query_open_labs(db, keywords)
        )

    async def list_lab_equipments(lab_id: int, keywords: str | None = None) -> str:
        return await asyncio.to_thread(
            _run_read_query,
            lambda db: _query_lab_equipments(db, lab_id, keywords),
        )

    return [
        StructuredTool.from_function(
            coroutine=list_open_labs,
            name="list_open_labs",
            description=(
                "查询数据库中 status=1（开放标记）的实验室，可按名称关键字筛选。"
                "这只表示实验室状态标记为开放，不代表任一具体时段有空位。"
            ),
            args_schema=_ListOpenLabsArgs,
        ),
        StructuredTool.from_function(
            coroutine=list_lab_equipments,
            name="list_lab_equipments",
            description=(
                "查询指定实验室当前登记的设备，可按设备名称筛选。"
                "设备 status=0 表示维修，status=1 表示正常；不得据此推断可预约数量。"
            ),
            args_schema=_ListLabEquipmentsArgs,
        ),
    ]
