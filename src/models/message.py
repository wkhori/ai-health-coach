from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ConversationTurn(BaseModel):
    id: UUID | None = None
    user_id: UUID
    role: str  # "user", "assistant", "system", "tool"
    content: str
    phase: str
    tool_calls: dict[str, Any] | None = None
    tool_results: dict[str, Any] | None = None
    token_count_input: int | None = None
    token_count_output: int | None = None
    turn_number: int = 0
    created_at: datetime = Field(default_factory=datetime.now)


class ConversationSummary(BaseModel):
    id: UUID | None = None
    user_id: UUID
    summary_text: str
    turns_covered_from: int
    turns_covered_to: int
    created_at: datetime = Field(default_factory=datetime.now)
