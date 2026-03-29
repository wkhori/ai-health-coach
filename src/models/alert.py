from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.models.enums import AlertUrgency


class ClinicianAlert(BaseModel):
    id: UUID | None = None
    user_id: UUID
    safety_audit_id: UUID | None = None
    alert_type: str  # "crisis", "clinical_boundary", "disengagement", "repeated_flags"
    urgency: AlertUrgency = AlertUrgency.ROUTINE
    status: str = "pending"  # "pending", "acknowledged", "resolved"
    message: str = ""
    acknowledged_at: datetime | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
