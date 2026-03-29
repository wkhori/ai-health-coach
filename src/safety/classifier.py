"""Tier 2: LLM-based safety classifier using ChatAnthropic with structured output.

Also contains the decide_action() function that maps SafetyResult -> SafetyAction
based on the decision thresholds.
"""

import structlog
from langchain_anthropic import ChatAnthropic

from src.models.enums import SafetyAction, SafetyClassificationType
from src.models.safety import SafetyResult

logger = structlog.get_logger(__name__)

_CLASSIFICATION_PROMPT = """You are a safety classifier for a wellness coaching application.

Analyze the following message and classify it as one of:
- "safe": General wellness, exercise, goal-setting, motivation, scheduling, encouragement
- "clinical": Medical advice, diagnosis, treatment recommendations, medication, dosage
- "crisis": Self-harm, suicidal ideation, immediate danger, severe mental distress
- "ambiguous": Could be interpreted as clinical or crisis but unclear

Also provide:
- confidence: How confident you are in the classification (0.0 to 1.0)
- categories: List of relevant category tags
- flagged_phrases: Specific phrases that triggered concern (empty list if safe)
- reasoning: Brief explanation of your classification

Message to classify:
{text}
"""


def tier2_classify(text: str) -> SafetyResult:
    """Classify text using the LLM safety classifier.

    Uses ChatAnthropic with structured output to return a SafetyResult.
    Temperature is 0.0 for deterministic classification. Max tokens is 256.
    """
    llm = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        temperature=0.0,
        max_tokens=256,
    )

    chain = llm.with_structured_output(SafetyResult)
    prompt = _CLASSIFICATION_PROMPT.format(text=text)

    result = chain.invoke(prompt)

    logger.info(
        "tier2_classification",
        classification=result.classification,
        confidence=result.confidence,
        reasoning=result.reasoning,
    )

    return result


def decide_action(result: SafetyResult) -> SafetyAction:
    """Map a SafetyResult to a SafetyAction based on decision thresholds.

    Decision thresholds:
    - confidence >= 0.8 AND safe -> PASS
    - crisis (any confidence) -> BLOCK + alert_clinician(urgent)
    - clinical AND confidence >= 0.6 -> REWRITE
    - confidence < 0.6 -> BLOCK (err on caution)
    """
    # Crisis always blocks, regardless of confidence
    if result.classification == SafetyClassificationType.CRISIS:
        logger.warning("safety_action_blocked_crisis", confidence=result.confidence)
        return SafetyAction.BLOCKED

    # Safe with high confidence passes
    if result.classification == SafetyClassificationType.SAFE and result.confidence >= 0.8:
        return SafetyAction.PASSED

    # Clinical with sufficient confidence gets rewritten
    if result.classification == SafetyClassificationType.CLINICAL and result.confidence >= 0.6:
        return SafetyAction.REWRITTEN

    # Everything else (low confidence, ambiguous) -> BLOCK as a precaution
    logger.info(
        "safety_action_blocked_caution",
        classification=result.classification,
        confidence=result.confidence,
    )
    return SafetyAction.BLOCKED
