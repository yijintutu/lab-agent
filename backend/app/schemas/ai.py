from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    thread_id: UUID | None = None

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("消息内容不能为空")
        return value.strip()


class ChatSource(BaseModel):
    source: str
    kind: Literal["policy", "lab", "equipment", "document"]
    score: float = Field(ge=0, le=1)


class ChatResponse(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: str = Field(min_length=1)
    sources: list[ChatSource] = Field(default_factory=list)
    thread_id: UUID
    pending_confirmation: bool = False


class KnowledgeIndexResponse(BaseModel):
    collection_name: str
    document_count: int
    chunk_count: int
    indexed_at: str
