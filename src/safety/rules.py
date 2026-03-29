"""Tier 1: Rule-based pre-filter for the safety system.

Handles FAST PASS (clearly safe) and FAST BLOCK (clearly unsafe/crisis) cases
without invoking the LLM. Returns None when no rule matches (defer to Tier 2).
"""

import re

import structlog

from src.models.enums import SafetyClassificationType
from src.models.safety import SafetyResult

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# FAST PASS patterns — positive reinforcement, goal/reminder confirmations
# ---------------------------------------------------------------------------
_POSITIVE_REINFORCEMENT_PATTERNS = [
    re.compile(
        r"\b(great|good|nice|awesome|fantastic|excellent|wonderful|amazing)\s+(job|work)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bkeep\s+it\s+up\b", re.IGNORECASE),
    re.compile(r"\bwell\s+done\b", re.IGNORECASE),
    re.compile(r"\bproud\s+of\s+you\b", re.IGNORECASE),
    re.compile(
        r"\byou['']?re\s+doing\s+(great|amazing|awesome|wonderful|fantastic)\b", re.IGNORECASE
    ),
    re.compile(r"\bway\s+to\s+go\b", re.IGNORECASE),
    re.compile(r"\bkeep\s+up\s+the\s+(great|good)\s+work\b", re.IGNORECASE),
]

_GOAL_CONFIRMATION_PATTERNS = [
    re.compile(r"\byour\s+goal\s+has\s+been\s+set\b", re.IGNORECASE),
    re.compile(r"\bgoal\s+confirmed\b", re.IGNORECASE),
    re.compile(r"\breminder\s+(has\s+been\s+)?set\b", re.IGNORECASE),
    re.compile(r"\blet['']?s\s+track\s+your\s+progress\b", re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# FAST BLOCK — crisis keywords
# ---------------------------------------------------------------------------
_CRISIS_PATTERNS = [
    re.compile(r"\bkill\s+my\s*self\b", re.IGNORECASE),
    re.compile(r"\bwant\s+to\s+die\b", re.IGNORECASE),
    re.compile(r"\bsuicid(al|e)\b", re.IGNORECASE),
    re.compile(r"\bself[- ]?harm\b", re.IGNORECASE),
    re.compile(r"\bend\s+my\s+life\b", re.IGNORECASE),
    re.compile(r"\btake\s+my\s+(own\s+)?life\b", re.IGNORECASE),
    re.compile(r"\bdon['']?t\s+want\s+to\s+(be\s+)?alive\b", re.IGNORECASE),
    re.compile(r"\bhurt\s+my\s*self\b", re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# FAST BLOCK — clinical content (dosage, diagnostic)
# ---------------------------------------------------------------------------
_DOSAGE_PATTERN = re.compile(
    r"\b\d+\s*(mg|mcg|ml|units?|tablets?|pills?|caps?)\b",
    re.IGNORECASE,
)

_DIAGNOSTIC_PATTERNS = [
    re.compile(r"\byou\s+have\b", re.IGNORECASE),
    re.compile(r"\byou\s+might\s+have\b", re.IGNORECASE),
    re.compile(r"\bsymptoms?\s+suggest\b", re.IGNORECASE),
    re.compile(r"\bdiagnosed\s+with\b", re.IGNORECASE),
]


def tier1_classify(text: str) -> SafetyResult | None:
    """Apply rule-based pre-filter to text.

    Returns:
        SafetyResult if a rule matches (FAST PASS or FAST BLOCK).
        None if no rule matches (text should go to Tier 2 LLM classifier).
    """
    # --- FAST BLOCK: Crisis ---
    for pattern in _CRISIS_PATTERNS:
        match = pattern.search(text)
        if match:
            logger.warning("tier1_crisis_detected", flagged_phrase=match.group())
            return SafetyResult(
                classification=SafetyClassificationType.CRISIS,
                confidence=1.0,
                categories=["crisis"],
                flagged_phrases=[match.group()],
                reasoning=f"Tier 1 rule: crisis keyword matched — '{match.group()}'",
            )

    # --- FAST BLOCK: Clinical — dosage ---
    dosage_match = _DOSAGE_PATTERN.search(text)
    if dosage_match:
        logger.info("tier1_clinical_dosage", flagged_phrase=dosage_match.group())
        return SafetyResult(
            classification=SafetyClassificationType.CLINICAL,
            confidence=0.95,
            categories=["dosage"],
            flagged_phrases=[dosage_match.group()],
            reasoning=f"Tier 1 rule: dosage pattern matched — '{dosage_match.group()}'",
        )

    # --- FAST BLOCK: Clinical — diagnostic language ---
    for pattern in _DIAGNOSTIC_PATTERNS:
        match = pattern.search(text)
        if match:
            logger.info("tier1_clinical_diagnostic", flagged_phrase=match.group())
            return SafetyResult(
                classification=SafetyClassificationType.CLINICAL,
                confidence=0.95,
                categories=["diagnostic_language"],
                flagged_phrases=[match.group()],
                reasoning=f"Tier 1 rule: diagnostic language matched — '{match.group()}'",
            )

    # --- FAST PASS: Positive reinforcement ---
    for pattern in _POSITIVE_REINFORCEMENT_PATTERNS:
        if pattern.search(text):
            return SafetyResult(
                classification=SafetyClassificationType.SAFE,
                confidence=0.99,
                categories=["positive_reinforcement"],
                flagged_phrases=[],
                reasoning="Tier 1 rule: positive reinforcement pattern matched",
            )

    # --- FAST PASS: Goal/reminder confirmation ---
    for pattern in _GOAL_CONFIRMATION_PATTERNS:
        if pattern.search(text):
            return SafetyResult(
                classification=SafetyClassificationType.SAFE,
                confidence=0.99,
                categories=["goal_confirmation"],
                flagged_phrases=[],
                reasoning="Tier 1 rule: goal/reminder confirmation pattern matched",
            )

    # No rule matched — defer to Tier 2
    return None
