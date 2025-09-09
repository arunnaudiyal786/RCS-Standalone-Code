from langchain_core.tools import tool
from langgraph.types import Command
from models.data_models import MessagesState


def create_handoff_tool(*, agent_name: str, description: str | None = None):
    name = f"transfer_to_{agent_name}"
    description = description or f"Ask {agent_name} for help."

    @tool(name, description=description)
    def handoff_tool(
        state: MessagesState,
        tool_call_id: str,
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


# Create handoff tools
assign_to_info_retriever_agent = create_handoff_tool(
    agent_name="MM Information Retrieval Agent",
    description="Assign task to a researcher agent.",
)

assign_to_execution_agent = create_handoff_tool(
    agent_name="MM Execution Agent",
    description="Assign task to a math agent.",
)

assign_to_validation_agent = create_handoff_tool(
    agent_name="MM Validation Agent",
    description="Assign task to a validation agent.",
)