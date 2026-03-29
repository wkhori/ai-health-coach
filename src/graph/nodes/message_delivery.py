"""Output handler — pass/rewrite/block based on safety result."""

from typing import Any

from langchain_core.messages import AIMessage, SystemMessage

from src.graph.state import HealthCoachState
from src.models.enums import SafetyAction

CRISIS_RESPONSE = (
    "I can hear that you're going through a really difficult time, and I want you to know "
    "that you're not alone. Please reach out for immediate support:\n\n"
    "- **988 Suicide & Crisis Lifeline**: Call or text 988 (available 24/7)\n"
    "- **Crisis Text Line**: Text HOME to 741741\n\n"
    "Your care team has been alerted and will follow up with you. "
    "You matter, and help is available right now."
)

BLOCKED_RESPONSE = (
    "I want to make sure I give you the best support. Let me rephrase — "
    "for any medical questions or concerns, please reach out to your care team directly. "
    "I'm here to help you with your exercise goals! What can we work on today?"
)


def route_by_safety(state: HealthCoachState) -> str:
    """Route based on safety classification result.

    Returns one of: 'passed', 'rewritten', 'blocked', 'escalated'
    """
    safety_result = state.get("safety_result", {})
    action = safety_result.get("action", SafetyAction.PASSED.value)

    route_map = {
        SafetyAction.PASSED.value: "passed",
        SafetyAction.REWRITTEN.value: "rewritten",
        SafetyAction.BLOCKED.value: "blocked",
        SafetyAction.ESCALATED.value: "escalated",
    }
    return route_map.get(action, "passed")


def output_passed(state: HealthCoachState) -> dict:
    """Pass through the original message unchanged."""
    messages = state.get("messages", [])
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "ai" and hasattr(msg, "content"):
            return {"response_text": msg.content}
    return {"response_text": ""}


def output_rewritten(state: HealthCoachState) -> dict:
    """Replace the message with a safe rewrite."""
    return {
        "messages": [AIMessage(content=BLOCKED_RESPONSE)],
        "response_text": BLOCKED_RESPONSE,
    }


def output_blocked(state: HealthCoachState) -> dict:
    """Block the message entirely with a safe response."""
    return {
        "messages": [AIMessage(content=BLOCKED_RESPONSE)],
        "response_text": BLOCKED_RESPONSE,
    }


def output_escalated(state: HealthCoachState) -> dict:
    """Replace message with crisis response and alert clinician."""
    return {
        "messages": [AIMessage(content=CRISIS_RESPONSE)],
        "response_text": CRISIS_RESPONSE,
    }


_RETRY_AUGMENT_PROMPT = (
    "IMPORTANT: Your previous response was flagged by the safety system. "
    "Rephrase your response focusing ONLY on general wellness, exercise, "
    "and goal-setting. Do NOT mention medical conditions, medications, "
    "diagnoses, or treatments. Redirect clinical questions to the care team."
)


async def retry_with_constraints(state: HealthCoachState, *, llm: Any = None) -> dict:
    """Retry a blocked message with an augmented safety-focused prompt."""
    if not llm:
        return {
            "messages": [AIMessage(content=BLOCKED_RESPONSE)],
            "response_text": BLOCKED_RESPONSE,
            "retry_count": state.get("retry_count", 0) + 1,
        }

    messages = list(state.get("messages", []))
    # Prepend safety augmentation to force compliance
    augmented_messages = [SystemMessage(content=_RETRY_AUGMENT_PROMPT)] + messages

    response = await llm.ainvoke(augmented_messages)
    result: dict[str, Any] = {
        "messages": [response],
        "retry_count": state.get("retry_count", 0) + 1,
    }

    if hasattr(response, "content") and response.content:
        result["response_text"] = response.content

    return result
