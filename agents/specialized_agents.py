from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from config.settings import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_MAX_TOKENS
from tools.ticket_tools import retrieve_similar_tickets, execute_resolution_step, validate_resolution
from tools.handoff_tools import assign_to_info_retriever_agent_with_task_description, assign_to_execution_agent_with_task_description, assign_to_validation_agent_with_task_description, assign_to_info_retriever_agent_with_handoff, assign_to_execution_agent_with_handoff, assign_to_validation_agent_with_handoff


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
        temperature=OPENAI_TEMPERATURE
    ),
    tools=[assign_to_info_retriever_agent_with_task_description, assign_to_execution_agent_with_task_description, assign_to_validation_agent_with_task_description],
    prompt="""You are a Domain Supervisor Agent orchestrating ticket resolution through three specialized agents:

AGENTS:
- Information Retrieval Agent: Gathers historical tickets and knowledge base information
- Execution Agent: Implements resolution steps (INSERT, UPDATE, DELETE, CONFIGURE actions)  
- Validation Agent: Verifies resolution success (VERIFY actions) and validates implementations

WORKFLOW:
1. Analyze the reasoning output: solution_steps, action_types, complexity_level, confidence_score
2. Assign tasks strategically:
   - Info Retrieval: For complex tickets needing historical context or similar cases
   - Execution: For implementation steps with action_types INSERT/UPDATE/DELETE/CONFIGURE
   - Validation: For VERIFY action_types and final quality checks
3. Work sequentially - one agent at a time, never parallel
4. Provide relevant reasoning step details when assigning tasks
5. After all agents complete, transfer to report_agent

Example: For VERIFY→INSERT→VERIFY steps:
1. Assign initial VERIFY to Execution Agent
2. Assign INSERT to Execution Agent  
3. Assign final VERIFY to Validation Agent

Do not perform any work yourself - only coordinate and assign tasks.""",
    name="Domain Supervisor Agent",
)