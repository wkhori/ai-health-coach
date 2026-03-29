from enum import StrEnum


class PhaseState(StrEnum):
    PENDING = "PENDING"
    ONBOARDING = "ONBOARDING"
    ACTIVE = "ACTIVE"
    RE_ENGAGING = "RE_ENGAGING"
    DORMANT = "DORMANT"


class InteractionType(StrEnum):
    CELEBRATION = "celebration"
    NUDGE = "nudge"
    CHECK_IN = "check_in"
    RE_ENGAGE = "re_engage"
    CRISIS_REDIRECT = "crisis_redirect"


class SafetyClassificationType(StrEnum):
    SAFE = "safe"
    CLINICAL = "clinical"
    CRISIS = "crisis"
    AMBIGUOUS = "ambiguous"


class SafetyAction(StrEnum):
    PASSED = "passed"
    REWRITTEN = "rewritten"
    BLOCKED = "blocked"
    ESCALATED = "escalated"


class AlertUrgency(StrEnum):
    ROUTINE = "routine"
    URGENT = "urgent"
