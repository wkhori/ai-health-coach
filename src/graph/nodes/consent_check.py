"""Consent gate node — verifies consent on every interaction."""

from langchain_core.messages import AIMessage

from src.graph.state import HealthCoachState

CONSENT_REQUEST_MESSAGE = (
    "Before we can begin, I need your consent to participate in this wellness "
    "coaching program. Your privacy and autonomy are important to me.\n\n"
    "By giving consent, you agree to:\n"
    "- Receive wellness coaching support for your exercise program\n"
    "- Have your conversation data stored securely\n"
    "- Allow your care team to be notified if safety concerns arise\n\n"
    "You can revoke your consent at any time. Would you like to proceed?"
)


def consent_gate_router(state: HealthCoachState) -> str:
    """Route based on consent status.

    Returns 'has_consent' or 'no_consent' for conditional edge routing.
    """
    if state.get("consent_given", False):
        return "has_consent"
    return "no_consent"


def request_consent(state: HealthCoachState) -> dict:
    """Return a consent request message when user has not given consent."""
    return {
        "messages": [AIMessage(content=CONSENT_REQUEST_MESSAGE)],
        "response_text": CONSENT_REQUEST_MESSAGE,
    }
