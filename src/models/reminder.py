from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class Reminder(BaseModel):
    id: UUID | None = None
    user_id: UUID
    reminder_type: str = "follow_up"  # "follow_up", "goal_check", "custom"
    message_template: str = ""
    scheduled_at: datetime | None = None
    due_at: datetime | None = None
    sent_at: datetime | None = None
    status: str = "pending"  # "pending", "sent", "failed", "cancelled"
    retry_count: int = 0
    attempt_number: int = 1  # 1, 2, 3 for re-engagement tracking
    created_at: datetime = Field(default_factory=datetime.now)
