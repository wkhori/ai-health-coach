from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class Milestone(BaseModel):
    id: UUID | None = None
    goal_id: UUID
    user_id: UUID
    title: str
    description: str = ""
    week_number: int
    completed: bool = False
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.now)


class Goal(BaseModel):
    id: UUID | None = None
    user_id: UUID
    title: str
    description: str = ""
    frequency: str = ""
    target_per_week: int = 0
    confirmed: bool = False
    status: str = "active"
    target_date: date | None = None
    milestones: list[Milestone] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
