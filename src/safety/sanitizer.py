"""Input sanitizer — strips control characters, detects injection patterns.

Layer 1 of prompt injection defense. Does NOT block; flags for downstream safety classifier.
"""

import re

import structlog

logger = structlog.get_logger(__name__)

# Control characters to strip (C0 controls except \t \n \r)
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Zero-width characters
_ZERO_WIDTH_CHARS = {
    "\u200b",  # zero-width space
    "\u200c",  # zero-width non-joiner
    "\u200d",  # zero-width joiner
    "\u2060",  # word joiner
    "\ufeff",  # zero-width no-break space (BOM)
}

# Injection patterns — case-insensitive
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"ignore\s+(all\s+)?prior\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+", re.IGNORECASE),
    re.compile(r"^system\s*:", re.IGNORECASE | re.MULTILINE),
    re.compile(r"pretend\s+you\s+are", re.IGNORECASE),
    re.compile(r"act\s+as\s+if\s+you\s+are", re.IGNORECASE),
    re.compile(r"new\s+instructions?\s*:", re.IGNORECASE),
    re.compile(r"forget\s+(all\s+)?your\s+(previous\s+)?instructions", re.IGNORECASE),
    re.compile(r"override\s+(all\s+)?(previous\s+)?rules", re.IGNORECASE),
]


def sanitize_input(text: str) -> str:
    """Strip control characters and zero-width characters from input text.

    Preserves normal Unicode (accents, emoji, etc).
    """
    # Strip control characters
    result = _CONTROL_CHAR_RE.sub("", text)

    # Strip zero-width characters
    for char in _ZERO_WIDTH_CHARS:
        result = result.replace(char, "")

    return result


def detect_injection_patterns(text: str) -> list[str]:
    """Detect prompt injection patterns in input text.

    Returns a list of matched pattern descriptions. Empty list means no injection detected.
    Does NOT block — the safety classifier handles the decision.
    """
    matches: list[str] = []

    for pattern in _INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            matches.append(match.group())

    if matches:
        logger.warning("injection_patterns_detected", patterns=matches)

    return matches
