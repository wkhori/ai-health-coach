from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.models.enums import SafetyAction, SafetyClassificationType


class SafetyResult(BaseModel):
    classification: SafetyClassificationType
    confidence: float
    categories: list[str] = Field(default_factory=list)
    flagged_phrases: list[str] = Field(default_factory=list)
    reasoning: str = ""

    @field_validator("confidence")
    @classmethod
    def confidence_in_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v


class SafetyAuditEntry(BaseModel):
    id: UUID | None = None
    user_id: UUID
    conversation_turn_id: UUID | None = None
    input_text: str
    classification: SafetyClassificationType
    confidence: float
    categories: list[str] = Field(default_factory=list)
    flagged_phrases: list[str] = Field(default_factory=list)
    reasoning: str = ""
    action_taken: SafetyAction
    tier: str = "llm"  # "rule" or "llm"
    model_used: str = ""
    created_at: datetime = Field(default_factory=datetime.now)

    @field_validator("confidence")
    @classmethod
    def confidence_in_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v
