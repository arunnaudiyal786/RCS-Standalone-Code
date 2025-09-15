from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from config.settings import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_MAX_TOKENS
from config.constants import INFO_RETRIEVER_AGENT, EXECUTION_AGENT, VALIDATION_AGENT, REASONING_AGENT, REPORT_AGENT, SUPERVISOR_AGENT
from tools.ticket_tools import retrieve_similar_tickets, execute_resolution_step, validate_resolution
from tools.handoff_tools import assign_to_info_retriever_agent_with_handoff, assign_to_execution_agent_with_handoff, assign_to_validation_agent_with_handoff, assign_to_report_agent_with_handoff


def create_info_retriever_agent():
    """Create and return an Information Retrieval agent."""
    return create_react_agent(
        model=ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=OPENAI_TEMPERATURE,
            max_tokens=OPENAI_MAX_TOKENS
        ),
        tools=[retrieve_similar_tickets],
        prompt="""You are an Information Retrieval agent.
        
        Gather all relevant tickets from the vector database needed to resolve the ticket.""",
        name=INFO_RETRIEVER_AGENT
    )


def create_execution_agent():
    """Create and return an Execution agent."""
    return create_react_agent(
        model=ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=OPENAI_TEMPERATURE,
            max_tokens=OPENAI_MAX_TOKENS
        ),
        tools=[execute_resolution_step],
        prompt="""You are an Execution agent responsible for implementing resolution steps based on the tickets retrieved from the vector database.
        
        Execute each step carefully and report on the results. Ensure proper error handling.""",
        name=EXECUTION_AGENT
    )


def create_validation_agent():
    """Create and return a Validation agent."""
    return create_react_agent(
        model=ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=OPENAI_TEMPERATURE,
            max_tokens=OPENAI_MAX_TOKENS
        ),
        tools=[validate_resolution],
        prompt="""You are a Validation agent that verifies resolution success.
        
        Check that all steps were executed correctly and the issue is resolved. Provide confidence scores and recommendations.""",
        name=VALIDATION_AGENT
    )


def create_reasoning_agent():
    """Create and return a Reasoning agent."""
    return create_react_agent(
        model=ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=OPENAI_TEMPERATURE,
            max_tokens=OPENAI_MAX_TOKENS
        ),
        tools=[],
        prompt="""You are a Reasoning agent that reasons about the ticket.""",
        name=REASONING_AGENT
    )


def create_report_agent():
    """Create and return a Report agent."""
    return create_react_agent(
        model=ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=OPENAI_TEMPERATURE,
            max_tokens=OPENAI_MAX_TOKENS
        ),
        tools=[],
        prompt="""You are a report agent that reports the resolution of the ticket.""",
        name=REPORT_AGENT
    )


def create_supervisor_agent():
    """Create and return a Domain Supervisor agent."""
    return create_react_agent(
        model=ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=OPENAI_TEMPERATURE
        ),
        tools=[assign_to_info_retriever_agent_with_handoff, assign_to_execution_agent_with_handoff, assign_to_validation_agent_with_handoff, assign_to_report_agent_with_handoff],
        prompt="""You are a Domain Supervisor Agent orchestrating ticket resolution through four specialized agents:

AGENTS:
- Information Retrieval Agent: Gathers historical tickets and knowledge base information
- Execution Agent: Implements resolution steps (INSERT, UPDATE, DELETE, CONFIGURE actions)  
- Validation Agent: Verifies resolution success (VERIFY actions) and validates implementations
- Report Agent: Generates final resolution report and completes the workflow

WORKFLOW:
1. Analyze the reasoning output: solution_steps, action_types, complexity_level, confidence_score
2. Assign tasks strategically:
   - Info Retrieval: For the steps retrieved from the reasoning output , we need to retrieve the relevant information from the knowledge base.
   - Execution: For implementation steps with action_types INSERT/UPDATE/DELETE
   - Validation: For VERIFY action_types and final quality checks
3. Work sequentially - one agent at a time, never parallel
4. Provide relevant reasoning step details when assigning tasks
5. IMPORTANT: After all solution steps are completed by the appropriate agents, assign to Report Agent to generate final report and END the workflow

TERMINATION RULES:
- Track which reasoning steps have been completed
- Once all solution steps from reasoning output are addressed, assign to Report Agent
- Do NOT keep assigning tasks indefinitely
- The Report Agent will END the workflow automatically

Example: For VERIFY→INSERT→VERIFY steps:
1. Assign initial VERIFY to Validation Agent
2. Assign INSERT to Execution Agent  
3. Assign final VERIFY to Validation Agent
4. MANDATORY: Assign final report generation to Report Agent (workflow ends)

IMPORTANT: Always end by calling the Report Agent after completing all solution steps.

Do not perform any work yourself - only coordinate and assign tasks.""",
        name=SUPERVISOR_AGENT,
    )