from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class DataPointCreate(BaseModel):
    date: date
    value: float
    memo: Optional[str] = None


class DataPointUpdate(BaseModel):
    date: Optional[date] = None
    value: Optional[float] = None
    memo: Optional[str] = None


class DataPointOut(BaseModel):
    id: str
    date: date
    value: float
    memo: Optional[str] = None


class DataSummaryMetrics(BaseModel):
    total: float
    average: float
    max: float
    min: float


class DataSummary(BaseModel):
    period: str
    count: int
    metrics: DataSummaryMetrics
    trend: str


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str


class ConversationCreate(BaseModel):
    title: Optional[str] = None
    messages: list[ChatMessage]


class ConversationSummary(BaseModel):
    id: str
    title: str
    message_count: int
    created_at: datetime
    updated_at: datetime


class ConversationDetail(ConversationSummary):
    messages: list[ChatMessage]
