from typing import Annotated
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.types import Command, Send
from langgraph.prebuilt import InjectedState
from models.data_models import MessagesState
from config.constants import INFO_RETRIEVER_AGENT, EXECUTION_AGENT, VALIDATION_AGENT, REPORT_AGENT


def sanitize_tool_name(agent_name: str) -> str:
    """Convert agent name to valid tool name format (only letters, numbers, underscores, hyphens)"""
    # Replace spaces with underscores and remove other invalid characters
    sanitized = agent_name.replace(" ", "_").replace(".", "_")
    # Keep only alphanumeric characters, underscores, and hyphens
    sanitized = "".join(c for c in sanitized if c.isalnum() or c in "_-")
    return sanitized


def create_handoff_tool(*, agent_name: str, description: str | None = None):
    name = f"transfer_to_{sanitize_tool_name(agent_name)}"
    description = description or f"Ask {agent_name} for help."

    @tool(name, description=description)
    def handoff_tool() -> str:
        return f"Task assigned to {agent_name}. Proceeding with workflow."

    return handoff_tool


def create_task_description_handoff_tool(
    *, agent_name: str, description: str | None = None
):
    name = f"transfer_to_{sanitize_tool_name(agent_name)}"
    description = description or f"Ask {agent_name} for help."

    @tool(name, description=description)
    def handoff_tool(
        # this is populated by the supervisor LLM
        task_description: Annotated[
            str,
            "Description of what the next agent should do, including all of the relevant context.",
        ],
        # these parameters are ignored by the LLM
        state: Annotated[MessagesState, InjectedState],
    ) -> Command:
        task_description_message = {"role": "user", "content": task_description}
        
        # Ensure we have all the required state fields with proper defaults
        agent_input = {
            "messages": [task_description_message],
            "query_refinement_output": state.get("query_refinement_output"),
            "input_ticket": state.get("input_ticket"), 
            "ticket_refinement_output": state.get("ticket_refinement_output"),
            "reasoning_output": state.get("reasoning_output")
        }
        
        return Command(
            goto=[Send(agent_name, agent_input)],
            graph=Command.PARENT,
        )

    return handoff_tool

# Create task description handoff tools
assign_to_info_retriever_agent_with_task_description = create_task_description_handoff_tool(
    agent_name=INFO_RETRIEVER_AGENT,
    description="Assign task to a researcher agent.",
)

assign_to_execution_agent_with_task_description = create_task_description_handoff_tool(
    agent_name=EXECUTION_AGENT,
    description="Assign task to an execution agent.",
)

assign_to_validation_agent_with_task_description = create_task_description_handoff_tool(
    agent_name=VALIDATION_AGENT,
    description="Assign task to a validation agent.",
)

assign_to_report_agent_with_task_description = create_task_description_handoff_tool(
    agent_name=REPORT_AGENT,
    description="Assign task to generate final report and complete the workflow.",
)

# Create handoff tools
assign_to_info_retriever_agent_with_handoff = create_handoff_tool(
    agent_name=INFO_RETRIEVER_AGENT,
    description="Assign task to a researcher agent.",
)

assign_to_execution_agent_with_handoff = create_handoff_tool(
    agent_name=EXECUTION_AGENT,
    description="Assign task to an execution agent.",
)

assign_to_validation_agent_with_handoff = create_handoff_tool(
    agent_name=VALIDATION_AGENT,
    description="Assign task to a validation agent.",
)

assign_to_report_agent_with_handoff = create_handoff_tool(
    agent_name=REPORT_AGENT,
    description="Assign task to generate final report and complete the workflow.",
)