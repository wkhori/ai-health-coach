"""Safety classifier node — runs on every outbound message."""

from typing import Any

from src.graph.state import HealthCoachState
from src.models.enums import SafetyAction, SafetyClassificationType


def run_safety_check(
    state: HealthCoachState,
    *,
    safety_classifier: Any = None,
) -> dict:
    """Run the two-tier safety classifier on the last assistant message.

    The safety_classifier is injected for testability. It should be a callable
    that takes a string and returns a dict with:
        {classification, confidence, categories, action, reasoning}
    """
    # Get the last assistant message
    messages = state.get("messages", [])
    last_message_text = ""
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "ai" and hasattr(msg, "content"):
            last_message_text = msg.content
            break

    if not last_message_text:
        return {
            "safety_result": {
                "classification": SafetyClassificationType.SAFE.value,
                "confidence": 1.0,
                "categories": [],
                "action": SafetyAction.PASSED.value,
                "reasoning": "No assistant message to check.",
            },
        }

    if safety_classifier:
        result = safety_classifier(last_message_text)
        return {"safety_result": result}

    # Default: pass-through if no classifier provided
    return {
        "safety_result": {
            "classification": SafetyClassificationType.SAFE.value,
            "confidence": 1.0,
            "categories": [],
            "action": SafetyAction.PASSED.value,
            "reasoning": "No safety classifier configured.",
        },
    }
