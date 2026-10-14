from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("消息内容不能为空")
        return value.strip()


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=40)

    @model_validator(mode="after")
    def history_must_end_with_user(self):
        if self.messages[-1].role != "user":
            raise ValueError("最后一条消息必须来自用户")
        return self


class ChatSource(BaseModel):
    source: str
    kind: Literal["policy", "lab", "equipment", "document"]
    score: float = Field(ge=0, le=1)


class ChatResponse(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: str = Field(min_length=1)
    sources: list[ChatSource] = Field(default_factory=list)


class KnowledgeIndexResponse(BaseModel):
    collection_name: str
    document_count: int
    chunk_count: int
    indexed_at: str
