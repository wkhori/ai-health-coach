"""Re-engagement subgraph — context-aware re-engagement messages.

Built as a compiled StateGraph with agent-tool loop.
Tools bound: [set_goal, get_program_summary]
"""

import contextlib
from typing import Any

from langchain_core.messages import AIMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from src.graph.state import HealthCoachState

from src.prompts.re_engaging import RE_ENGAGING_PROMPT
from src.prompts.system import SYSTEM_PROMPT
from src.tools.definitions import get_program_summary, set_goal

# Tools available during re-engagement
RE_ENGAGING_TOOLS = [set_goal, get_program_summary]


def build_re_engaging_subgraph(llm: Any) -> Any:
    """Build and compile the re-engaging subgraph with tool loop.

    Flow: agent_node -> should_continue -> tools -> agent_node (loop)
                                        -> END (done)
    """
    bound_llm = llm.bind_tools(RE_ENGAGING_TOOLS)
    tool_node = ToolNode(RE_ENGAGING_TOOLS)

    async def agent_node(state: HealthCoachState) -> dict:
        """Invoke the LLM with re-engagement tools bound."""
        # Set user ID for tool operations
        import src.tools.definitions as tools_mod

        user_id = state.get("user_id", "")
        if user_id:
            tools_mod._CURRENT_USER_ID = user_id

        goals_summary = _format_goals_summary(state.get("active_goals", []))
        conversation_summary = state.get(
            "conversation_summary", "No previous summary available."
        )
        attempt_number = state.get("scheduled_message_type", "1")

        system_content = (
            SYSTEM_PROMPT
            + "\n\n"
            + RE_ENGAGING_PROMPT.format(
                display_name="there",
                goals_summary=goals_summary,
                progress_summary="Progress data from previous sessions.",
                conversation_summary=conversation_summary,
                days_inactive="a few",
                attempt_number=attempt_number,
            )
        )

        messages = [SystemMessage(content=system_content)] + list(
            state.get("messages", [])
        )

        response = await bound_llm.ainvoke(messages)
        result: dict[str, Any] = {"messages": [response]}

        if hasattr(response, "content") and response.content:
            result["response_text"] = response.content

        return result

    def should_continue(state: HealthCoachState) -> str:
        """Check if the last message has tool calls."""
        messages = state.get("messages", [])
        if not messages:
            return "done"
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "done"

    sg = StateGraph(HealthCoachState)
    sg.add_node("agent", agent_node)
    sg.add_node("tools", tool_node)

    sg.set_entry_point("agent")
    sg.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", "done": END},
    )
    sg.add_edge("tools", "agent")

    return sg.compile()


def build_re_engage_context(
    state: HealthCoachState,
    *,
    goal_repo: Any = None,
) -> dict:
    """Build context for re-engagement from goals, milestones, and summary."""
    goals = state.get("active_goals", [])
    if goal_repo and state.get("user_id"):
        from uuid import UUID

        with contextlib.suppress(Exception):
            goals = goal_repo.get_active_goals(UUID(state["user_id"]))

    return {
        "active_goals": goals,
    }


async def re_engage_agent(
    state: HealthCoachState,
    *,
    llm: Any = None,
) -> dict:
    """Fallback re-engagement agent for when no LLM is provided (tests)."""
    if not llm:
        msg = (
            "Hi there! I noticed we haven't connected in a while. "
            "I hope you're doing well. No pressure at all -- whenever you're ready, "
            "I'm here to help you get back on track with your exercises. "
            "Would you like to pick up where we left off?"
        )
        return {
            "messages": [AIMessage(content=msg)],
            "response_text": msg,
        }

    goals_summary = _format_goals_summary(state.get("active_goals", []))
    conversation_summary = state.get(
        "conversation_summary", "No previous summary available."
    )
    attempt_number = state.get("scheduled_message_type", "1")

    system_content = (
        SYSTEM_PROMPT
        + "\n\n"
        + RE_ENGAGING_PROMPT.format(
            display_name="there",
            goals_summary=goals_summary,
            progress_summary="Progress data from previous sessions.",
            conversation_summary=conversation_summary,
            days_inactive="a few",
            attempt_number=attempt_number,
        )
    )

    messages = [SystemMessage(content=system_content)] + list(
        state.get("messages", [])
    )

    response = await llm.ainvoke(messages)
    result: dict[str, Any] = {"messages": [response]}

    if hasattr(response, "content") and response.content:
        result["response_text"] = response.content

    return result


def should_continue_re_engage(state: HealthCoachState) -> str:
    """Check if the last message has tool calls that need execution."""
    messages = state.get("messages", [])
    if not messages:
        return "done"

    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    return "done"


def _format_goals_summary(goals: list[dict]) -> str:
    """Format goals for the re-engagement prompt."""
    if not goals:
        return "No previous goals recorded."

    lines = []
    for g in goals:
        lines.append(
            f"- {g.get('title', 'Untitled')}: {g.get('description', '')}"
        )
    return "\n".join(lines)
