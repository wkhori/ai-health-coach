"""Graph state schema for the AI Health Coach."""

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class HealthCoachState(TypedDict):
    """Canonical state type for the health coach graph."""

    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    profile_id: str
    phase: str  # PENDING, ONBOARDING, ACTIVE, RE_ENGAGING, DORMANT
    consent_given: bool
    conversation_summary: str
    turn_count: int
    active_goals: list[dict]
    adherence_summary: dict
    safety_result: dict  # {classification, confidence, categories, action}
    is_scheduled_message: bool
    scheduled_message_type: str
    response_text: str  # Final response after safety check
    retry_count: int  # 0 initially, incremented on blocked retry
