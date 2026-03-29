"""Active phase subgraph — main coaching loop.

Built as a compiled StateGraph with agent-tool loop.
Tools bound: [set_goal, set_reminder, get_program_summary, get_adherence_summary, alert_clinician]
"""

from typing import Any

from langchain_core.messages import AIMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from src.graph.state import HealthCoachState

from src.prompts.active import ACTIVE_PROMPT
from src.prompts.system import SYSTEM_PROMPT
from src.tools.definitions import (
    alert_clinician,
    get_adherence_summary,
    get_program_summary,
    set_goal,
    set_reminder,
)

# All 5 tools available during active phase
ACTIVE_TOOLS = [set_goal, set_reminder, get_program_summary, get_adherence_summary, alert_clinician]


def build_active_subgraph(llm: Any) -> Any:
    """Build and compile the active phase subgraph with tool loop.

    Flow: agent_node -> should_continue -> tools -> agent_node (loop)
                                        -> END (done)
    """
    bound_llm = llm.bind_tools(ACTIVE_TOOLS)
    tool_node = ToolNode(ACTIVE_TOOLS)

    async def agent_node(state: HealthCoachState) -> dict:
        """Invoke the LLM with all active tools bound."""
        # Set user ID for tool operations
        import src.tools.definitions as tools_mod

        user_id = state.get("user_id", "")
        if user_id:
            tools_mod._CURRENT_USER_ID = user_id

        goals_summary = _format_goals(state.get("active_goals", []))
        adherence_summary = _format_adherence(state.get("adherence_summary", {}))
        milestones_summary = _format_milestones(state.get("active_goals", []))
        conversation_summary = state.get(
            "conversation_summary", "No previous summary available."
        )

        system_content = (
            SYSTEM_PROMPT
            + "\n\n"
            + ACTIVE_PROMPT.format(
                display_name="there",
                goals_summary=goals_summary,
                adherence_summary=adherence_summary,
                milestones_summary=milestones_summary,
                conversation_summary=conversation_summary,
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


async def active_agent(
    state: HealthCoachState,
    *,
    llm: Any = None,
) -> dict:
    """Fallback active agent for when no LLM is provided (tests)."""
    if not llm:
        msg = "Great to see you! How are your exercises going today?"
        return {
            "messages": [AIMessage(content=msg)],
            "response_text": msg,
        }

    goals_summary = _format_goals(state.get("active_goals", []))
    adherence_summary = _format_adherence(state.get("adherence_summary", {}))
    milestones_summary = _format_milestones(state.get("active_goals", []))
    conversation_summary = state.get(
        "conversation_summary", "No previous summary available."
    )

    system_content = (
        SYSTEM_PROMPT
        + "\n\n"
        + ACTIVE_PROMPT.format(
            display_name="there",
            goals_summary=goals_summary,
            adherence_summary=adherence_summary,
            milestones_summary=milestones_summary,
            conversation_summary=conversation_summary,
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


def should_continue_active(state: HealthCoachState) -> str:
    """Check if the last message has tool calls that need execution."""
    messages = state.get("messages", [])
    if not messages:
        return "done"

    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    return "done"


def _format_goals(goals: list[dict]) -> str:
    """Format goals for the prompt."""
    if not goals:
        return "No active goals set yet."

    lines = []
    for g in goals:
        status = "confirmed" if g.get("confirmed") else "pending"
        lines.append(
            f"- {g.get('title', 'Untitled')} ({status}): {g.get('description', '')}"
        )
    return "\n".join(lines)


def _format_adherence(adherence: dict) -> str:
    """Format adherence summary for the prompt."""
    if not adherence:
        return "No adherence data available yet."

    rate = adherence.get("adherence_rate", 0)
    streak = adherence.get("current_streak", 0)
    return f"Adherence rate: {rate}% | Current streak: {streak} days"


def _format_milestones(goals: list[dict]) -> str:
    """Format milestones from all goals for the prompt."""
    milestones = []
    for g in goals:
        for m in g.get("milestones", []):
            status = "completed" if m.get("completed") else "upcoming"
            milestones.append(
                f"- Week {m.get('week_number', '?')}: {m.get('title', '')} ({status})"
            )

    if not milestones:
        return "No milestones set yet."
    return "\n".join(milestones)
