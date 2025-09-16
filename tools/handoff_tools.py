from typing import Annotated
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.types import Command
from langgraph.prebuilt import InjectedState
from langgraph.graph import StateGraph, START, MessagesState, END
from config.constants import INFO_RETRIEVER_AGENT, EXECUTION_AGENT, VALIDATION_AGENT, REPORT_AGENT

def create_handoff_tool(*, agent_name: str, description: str | None = None):
    name = f"transfer_to_{agent_name}"
    description = description or f"Ask {agent_name} for help."

    @tool(name, description=description)
    def handoff_tool(
        state: Annotated[MessagesState, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:
        tool_message = {
            "role": "tool",
            "content": f"Successfully transferred to {agent_name}",
            "name": name,
            "tool_call_id": tool_call_id,
        }
        return Command(
            goto=agent_name,  
            update={**state, "messages": state["messages"] + [tool_message]},  
            graph=Command.PARENT,  
        )

    return handoff_tool


# Create handoff tools for all specialized agents
assign_to_info_retriever = create_handoff_tool(
    agent_name=INFO_RETRIEVER_AGENT,
    description="Assign task to info retriever agent to gather historical tickets and schema info.",
)

assign_to_execution = create_handoff_tool(
    agent_name=EXECUTION_AGENT,
    description="Assign task to execution agent to implement resolution steps.",
)

assign_to_validation = create_handoff_tool(
    agent_name=VALIDATION_AGENT,
    description="Assign task to validation agent to verify resolution success.",
)

assign_to_report = create_handoff_tool(
    agent_name=REPORT_AGENT,
    description="Assign task to report agent to generate final resolution report.",
)


@tool("complete_workflow", description="Complete the workflow and end the ticket resolution process.")
def complete_workflow(
    state: Annotated[MessagesState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Complete the workflow after all tasks are finished."""
    tool_message = {
        "role": "tool",
        "content": "Workflow completed successfully. All tasks have been finished.",
        "name": "complete_workflow",
        "tool_call_id": tool_call_id,
    }
    return Command(
        goto=END,
        update={**state, "messages": state["messages"] + [tool_message]},
        graph=Command.PARENT,
    )