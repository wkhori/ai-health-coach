"""Conversation summarization node — runs every N turns."""

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from src.graph.state import HealthCoachState

SUMMARIZE_PROMPT = """\
Summarize the following conversation between a wellness coach and a patient. \
Focus on: exercise goals discussed, progress updates, barriers mentioned, \
action items agreed upon, and the patient's emotional state. \
Keep the summary under 200 tokens.
"""


def should_summarize(state: HealthCoachState, every_n: int = 6) -> bool:
    """Check if we should summarize based on turn count."""
    turn_count = state.get("turn_count", 0)
    return turn_count > 0 and turn_count % every_n == 0


async def summarize_conversation(
    state: HealthCoachState,
    *,
    llm: Any = None,
    summary_repo: Any = None,
    every_n: int = 6,
) -> dict:
    """Summarize the conversation if turn count is a multiple of every_n.

    Uses Haiku to generate a ~200 token summary of the conversation.
    """
    if not should_summarize(state, every_n):
        return {}

    messages = state.get("messages", [])
    if not messages:
        return {}

    # Build conversation text for summarization
    conversation_text = ""
    for msg in messages[-every_n * 2 :]:  # Last N*2 messages (user + assistant pairs)
        role = getattr(msg, "type", "unknown")
        content = getattr(msg, "content", "")
        if role == "human":
            conversation_text += f"Patient: {content}\n"
        elif role == "ai":
            conversation_text += f"Coach: {content}\n"

    if not conversation_text or not llm:
        return {}

    # Generate summary using the LLM
    summary_messages = [
        SystemMessage(content=SUMMARIZE_PROMPT),
        HumanMessage(content=conversation_text),
    ]

    response = await llm.ainvoke(summary_messages)
    summary_text = response.content if hasattr(response, "content") else str(response)

    # Persist summary
    if summary_repo and state.get("user_id"):
        import contextlib
        from uuid import UUID

        with contextlib.suppress(Exception):
            turn_count = state.get("turn_count", 0)
            summary_repo.create(
                user_id=UUID(state["user_id"]),
                summary_text=summary_text,
                turns_covered_from=max(0, turn_count - every_n),
                turns_covered_to=turn_count,
            )

    return {"conversation_summary": summary_text}
