from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.models.enums import PhaseState


class PatientProfile(BaseModel):
    id: UUID
    user_id: UUID
    display_name: str
    timezone: str = "UTC"
    phase: PhaseState = PhaseState.PENDING
    phase_updated_at: datetime | None = None
    consent_given_at: datetime | None = None
    consent_revoked_at: datetime | None = None
    consent_version: str | None = None
    onboarding_completed_at: datetime | None = None
    last_message_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @property
    def has_consent(self) -> bool:
        return self.consent_given_at is not None and self.consent_revoked_at is None
