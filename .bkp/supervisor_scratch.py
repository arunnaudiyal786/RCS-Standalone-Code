import uuid
import os
from typing import List, Dict, Optional, Annotated
from datetime import datetime
from dotenv import load_dotenv
import base64
from io import BytesIO

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_core.documents import Document
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command
from langgraph_supervisor import create_supervisor
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition
from pydantic import BaseModel, Field
from typing import Literal
import faiss
from IPython.display import Image, display

# Load environment variables
load_dotenv()

# Environment variables with defaults
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.1"))
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "4000"))




from langchain_core.messages import convert_to_messages
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

# Define the state type
class MessagesState(TypedDict):
    messages: List[HumanMessage | AIMessage | ToolMessage | SystemMessage]


def pretty_print_message(message, indent=False):
    pretty_message = message.pretty_repr(html=True)
    if not indent:
        print(pretty_message)
        return

    indented = "\n".join("\t" + c for c in pretty_message.split("\n"))
    print(indented)


def pretty_print_messages(update, last_message=False):
    is_subgraph = False
    if isinstance(update, tuple):
        ns, update = update
        # skip parent graph updates in the printouts
        if len(ns) == 0:
            return

        graph_id = ns[-1].split(":")[0]
        print(f"Update from subgraph {graph_id}:")
        print("\n")
        is_subgraph = True

    for node_name, node_update in update.items():
        update_label = f"Update from node {node_name}:"
        if is_subgraph:
            update_label = "\t" + update_label

        print(update_label)
        print("\n")

        messages = convert_to_messages(node_update["messages"])
        if last_message:
            messages = messages[-1:]

        for m in messages:
            pretty_print_message(m, indent=is_subgraph)
        print("\n")




# ===============================
# DATA MODELS
# ===============================

class ResolutionStep(BaseModel):
    step_number: int
    description: str
    estimated_time: str

class ResolutionPlan(BaseModel):
    steps: List[ResolutionStep]
    priority: str
    complexity: str

class TicketAnalysis(BaseModel):
    ticket_id: str
    similarity_score: float
    resolution_approach: str

class ValidationResult(BaseModel):
    is_valid: bool
    confidence_score: float
    issues_found: List[str]
    recommendations: List[str]


# ===============================
# VECTOR DATABASE SETUP
# ===============================

class TicketVectorStore:
    def __init__(self):
        # Initialize embeddings with environment variables
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=OPENAI_API_KEY,
            model="text-embedding-3-small"
        )
        
        # Create sample historical tickets
        sample_tickets = [
            "Login authentication failure - users unable to access system",
            "Database connection timeout errors in production environment",
            "Payment gateway integration returning 500 errors",
            "Email notification service not sending confirmations",
            "API rate limiting causing client timeouts",
            "SSL certificate expired causing HTTPS errors",
            "Memory leak in application server causing crashes",
            "Broken image uploads in user profile section",
            "Search functionality returning incorrect results",
            "Mobile app crashes on iOS devices during startup"
        ] * 100  # Simulate 1000 tickets
        
        # Create documents
        docs = [Document(page_content=ticket, metadata={"id": f"TICKET-{i+1}"}) 
                for i, ticket in enumerate(sample_tickets)]
        
        # Create FAISS vector store
        self.vectorstore = FAISS.from_documents(docs, self.embeddings)
    
    def search_similar_tickets(self, query: str, k: int = 10) -> List[Dict]:
        results = self.vectorstore.similarity_search_with_score(query, k=k)
        return [
            {
                "ticket_id": doc.metadata["id"],
                "content": doc.page_content,
                "similarity_score": float(score)
            }
            for doc, score in results
        ]

# Initialize vector store
vector_store = TicketVectorStore()


# ===============================
# TOOLS
# ===============================

@tool
def retrieve_similar_tickets(ticket_description: str) -> List[Dict]:
    """Retrieve top 10 most similar historical tickets from vector database."""
    return vector_store.search_similar_tickets(ticket_description, k=10)




@tool
def execute_resolution_step(step_description: str, step_number: int) -> Dict:
    """Execute a specific resolution step."""
    return {
        "step_number": step_number,
        "status": "completed",
        "execution_time": "25 minutes",
        "output": f"Successfully executed: {step_description}",
        "next_action": "Proceed to validation"
    }

@tool
def validate_resolution(ticket_id: str, executed_steps: str) -> ValidationResult:
    """Validate that the resolution steps were successful."""
    return ValidationResult(
        is_valid=True,
        confidence_score=0.92,
        issues_found=[],
        recommendations=["Monitor system for 24 hours", "Document solution in knowledge base"]
    )

@tool
def refine_query(query: str) -> str:
    """
    Refine the input query to make it clearer and more understandable.
    """
    # For now, simply return the original query.
    # In a real implementation, you could use an LLM or rules to rewrite the query.
    return query



# ===============================
# HANDOFF TOOLS
# ===============================


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




# ===============================
# HANDOFF TOOLS
# ===============================

# Handoffs
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



# ===============================
# SPECIALIZED AGENTS
# ===============================

# Info Retriever Agent
info_retriever = create_react_agent(
    model=ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=OPENAI_TEMPERATURE,
        max_tokens=OPENAI_MAX_TOKENS
    ),
    tools=[retrieve_similar_tickets],
    prompt="""You are an Information Retrieval agent.
    
    Gather all relevant tickets from the vector database needed to resolve the ticket.""",
    name="MM Information Retrieval Agent"
)

# Execution Agent
execution_agent = create_react_agent(
    model=ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=OPENAI_TEMPERATURE,
        max_tokens=OPENAI_MAX_TOKENS
    ),
    tools=[execute_resolution_step],
    prompt="""You are an Execution agent responsible for implementing resolution steps based on the tickets retrieved from the vector database.
    
    Execute each step carefully and report on the results. Ensure proper error handling.""",
    name="MM Execution Agent"
)

# Validation Agent
validation_agent = create_react_agent(
    model=ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=OPENAI_TEMPERATURE,
        max_tokens=OPENAI_MAX_TOKENS
    ),
    tools=[validate_resolution],
    prompt="""You are a Validation agent that verifies resolution success.
    
    Check that all steps were executed correctly and the issue is resolved. Provide confidence scores and recommendations.""",
        name="MM Validation Agent"
)

reasoning_agent = create_react_agent(
    model=ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=OPENAI_TEMPERATURE,
        max_tokens=OPENAI_MAX_TOKENS
    ),
    tools=[],
    prompt="""You are a Reasoning agent that reasons about the ticket.""",
    name="Reasoning Agent"
)

report_agent = create_react_agent(
    model=ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=OPENAI_TEMPERATURE,
        max_tokens=OPENAI_MAX_TOKENS
    ),
    # tools=[review_resolution],
    tools=[],
    prompt="""You are a report agent that reports the resolution of the ticket.""",
    name="MM Report Agent"
)

supervisor_agent = create_react_agent(
    model=ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=OPENAI_TEMPERATURE,
        max_tokens=OPENAI_MAX_TOKENS
    ),
    tools=[assign_to_info_retriever_agent, assign_to_execution_agent, assign_to_validation_agent],
    prompt=(
        "You are a supervisor managing three agents:\n"
        "- a info_retriever agent. Assign info_retriever-related tasks to this agent\n"
        "- a execution agent. Assign execution-related tasks to this agent\n"
        "- a validation agent. Assign validation-related tasks to this agent\n"
        "After all agents complete their work, transfer to report_agent for final reporting.\n"
        "Assign work to one agent at a time, do not call agents in parallel.\n"
        "Do not do any work yourself."
    ),
    name="Domain Supervisor Agent",
)

def pattern_analysis(state: MessagesState):
    return {"messages": [AIMessage(content="Analyzing pattern...")]}

def label_analysis(state: MessagesState):
    return {"messages": [AIMessage(content="Analyzing labels...")]}

def query_refinement(state: MessagesState) -> Literal["Refine Query Step", "Label Analysis Step"]:
    # Check if query needs refinement based on length or complexity
    last_message = state["messages"][-1] if state["messages"] else None
    if last_message and hasattr(last_message, 'content'):
        query = last_message.content
        # Simple heuristic: if query is short or seems incomplete, refine it
        if len(query.strip()) < 20 or query.strip().endswith('?'):
            return "Refine Query Step"
    return "Label Analysis Step"


from langgraph.graph import END

# Define the multi-agent supervisor graph
supervisor = (
    StateGraph(MessagesState)
    .add_node("Query Refinement Check", query_refinement)
    .add_node("Refine Query Step", refine_query)
    .add_node("Pattern Analysis Step", pattern_analysis)
    .add_node("Label Analysis Step", label_analysis)
    .add_node(reasoning_agent)
    .add_node(supervisor_agent, destinations=("MM Information Retrieval Agent", "MM Execution Agent", "MM Validation Agent", "MM Report Agent"))
    .add_node(info_retriever)
    .add_node(execution_agent)
    .add_node(validation_agent)
    .add_node(report_agent)
    .add_edge(START, "Query Refinement Check")
    .add_conditional_edges("Query Refinement Check",query_refinement )
    # .add_edge("Query Refinement Check", "Refine Query Step")
    .add_edge("Query Refinement Check", "Label Analysis Step")
    .add_edge("Refine Query Step", "Label Analysis Step")
    .add_edge("Label Analysis Step", "Pattern Analysis Step")
    .add_edge("Pattern Analysis Step", "Reasoning Agent")
    .add_edge("Reasoning Agent", "Domain Supervisor Agent")
    .add_edge("MM Information Retrieval Agent", "Domain Supervisor Agent")
    .add_edge("MM Execution Agent", "Domain Supervisor Agent")
    .add_edge("MM Validation Agent", "Domain Supervisor Agent")
    .add_edge("MM Report Agent", END)
    .compile()
)

from IPython.display import display, Image

# Save the graph image to a file
graph_image = supervisor.get_graph().draw_mermaid_png()
with open("supervisor_graph.png", "wb") as f:
    f.write(graph_image)

print("Graph saved as 'supervisor_graph.png'")

# Optionally open it automatically (macOS)
import subprocess
subprocess.run(["open", "supervisor_graph.png"])