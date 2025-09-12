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
from pydantic import BaseModel, Field
import faiss
from IPython.display import Image, display


# Load environment variables from .env file
load_dotenv()

# ===============================
# CONFIGURATION
# ===============================

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required. Please set it in your .env file.")

# Optional configuration with defaults
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.1"))
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "4000"))


from langchain_core.messages import convert_to_messages


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
    name="info_retriever"
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
    name="execution_agent"
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
    name="validation_agent"
)



# ===============================
# MAIN SUPERVISOR SYSTEM
# ===============================


# Main Supervisor
main_supervisor = create_supervisor(
    agents=[info_retriever, execution_agent, validation_agent],
    model=ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=OPENAI_TEMPERATURE,
        max_tokens=OPENAI_MAX_TOKENS
    ),
    prompt="""You are the Main Supervisor for the Agentic RAG Ticket Resolution System.

    You are a supervisor managing three agents:
    - info_retriever: Assign research and information gathering tasks to this agent
    - execution_agent: Assign execution and implementation tasks to this agent  
    - validation_agent: Assign validation and verification tasks to this agent
    
    Assign work to one agent at a time, do not call agents in parallel.
    Do not do any work yourself.""",
    output_mode="full_history"
).compile(checkpointer=InMemorySaver())

display(Image(main_supervisor.get_graph().draw_mermaid_png()))


# ===============================
# EXAMPLE USAGE
# ===============================

if __name__ == "__main__":
    import sys

    # Stream the conversation
    final_chunk = None
    for chunk in main_supervisor.stream(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Resolve this ticket: Users are experiencing login failures with timeout errors when trying to access the application",
                }
            ]
        },
        config={"configurable": {"thread_id": "ticket_resolution_1"}}
    ):
        pretty_print_messages(chunk, last_message=True)
        final_chunk = chunk

    # Access the final messages properly
    if final_chunk:
        # The chunk structure contains the agent updates, not a main_supervisor key
        print("\n=== Final Message History ===")
        for node_name, node_update in final_chunk.items():
            if "messages" in node_update:
                print(f"\n--- {node_name} ---")
                for msg in node_update["messages"]:
                    print(f"{msg.type}: {msg.content}")
    else:
        print("No messages received from the supervisor.")