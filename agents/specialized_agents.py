from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from config.settings import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_MAX_TOKENS
from tools.ticket_tools import retrieve_similar_tickets, execute_resolution_step, validate_resolution
from tools.handoff_tools import assign_to_info_retriever_agent, assign_to_execution_agent, assign_to_validation_agent


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