"""Onboarding subgraph — guides new patients through goal setting.

Built as a compiled StateGraph with agent-tool loop.
Tools bound: [set_goal]
"""

from typing import Any

from langchain_core.messages import AIMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from src.graph.state import HealthCoachState
from src.prompts.onboarding import ONBOARDING_PROMPT
from src.prompts.system import SYSTEM_PROMPT
from src.tools.definitions import set_goal

# Tools available during onboarding
ONBOARDING_TOOLS = [set_goal]


def build_onboarding_subgraph(llm: Any) -> Any:
    """Build and compile the onboarding subgraph with tool loop.

    Flow: agent_node -> should_continue -> tools -> agent_node (loop)
                                        -> END (done)
    """
    bound_llm = llm.bind_tools(ONBOARDING_TOOLS)
    tool_node = ToolNode(ONBOARDING_TOOLS)

    async def agent_node(state: HealthCoachState) -> dict:
        """Invoke the LLM with bound tools."""
        # Set user ID for tool operations
        import src.tools.definitions as tools_mod

        user_id = state.get("user_id", "")
        if user_id:
            tools_mod._CURRENT_USER_ID = user_id

        display_name = "there"
        system_content = SYSTEM_PROMPT + "\n\n" + ONBOARDING_PROMPT.format(
            display_name=display_name
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


async def onboard_agent(
    state: HealthCoachState,
    *,
    llm: Any = None,
) -> dict:
    """Fallback onboarding agent for when no LLM is provided (tests)."""
    if not llm:
        msg = "Welcome! I'm your wellness coach. Let's set up your first exercise goal together. What would you like to achieve?"
        return {
            "messages": [AIMessage(content=msg)],
            "response_text": msg,
        }

    # Build system prompt with patient context
    display_name = "there"
    system_content = SYSTEM_PROMPT + "\n\n" + ONBOARDING_PROMPT.format(
        display_name=display_name
    )
    messages = [SystemMessage(content=system_content)] + list(
        state.get("messages", [])
    )

    response = await llm.ainvoke(messages)
    result: dict[str, Any] = {"messages": [response]}

    if hasattr(response, "content") and response.content:
        result["response_text"] = response.content

    return result


def check_onboarding_complete(state: HealthCoachState) -> dict:
    """Check if onboarding is complete (at least 1 confirmed goal)."""
    active_goals = state.get("active_goals", [])
    has_confirmed = any(g.get("confirmed", False) for g in active_goals)

    if has_confirmed:
        return {"phase": "ACTIVE"}
    return {}


def should_continue_onboarding(state: HealthCoachState) -> str:
    """Check if the last message has tool calls that need execution."""
    messages = state.get("messages", [])
    if not messages:
        return "done"

    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    return "done"
