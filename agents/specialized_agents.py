from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from config.settings import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_MAX_TOKENS
from config.constants import INFO_RETRIEVER_AGENT, EXECUTION_AGENT, VALIDATION_AGENT, REASONING_AGENT, REPORT_AGENT
from tools.ticket_tools import retrieve_similar_tickets, validate_resolution, retrieve_table_schema_info, get_table_info, insert_row_to_text_file, update_value_in_text_file
from tools.handoff_tools import complete_workflow
from tools.report_tools import save_report_to_markdown
from models.data_models import ReasoningOutput, InfoRetrieverOutput, ExecutionOutput, ValidationOutput, ReportOutput


def create_info_retriever_agent():
    """Create and return an Information Retrieval agent."""
    # Load info retriever prompt from file
    with open('prompts/info_retriever_agent.txt', 'r') as f:
        info_retriever_prompt = f.read()
    
    return create_react_agent(
        model=ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=OPENAI_TEMPERATURE,
            max_tokens=OPENAI_MAX_TOKENS
        ),
        tools=[retrieve_similar_tickets, retrieve_table_schema_info, get_table_info],
        prompt=info_retriever_prompt,
        name=INFO_RETRIEVER_AGENT,
        response_format=InfoRetrieverOutput
    )


def create_execution_agent():
    """Create and return an Execution agent."""
    # Load execution prompt from file
    with open('prompts/execution_agent.txt', 'r') as f:
        execution_prompt = f.read()
    
    return create_react_agent(
        model=ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=OPENAI_TEMPERATURE,
            max_tokens=OPENAI_MAX_TOKENS
        ),
        tools=[insert_row_to_text_file, update_value_in_text_file],
        prompt=execution_prompt,
        name=EXECUTION_AGENT
    )


def create_validation_agent():
    """Create and return a Validation agent."""
    # Load validation prompt from file
    with open('prompts/validation_agent.txt', 'r') as f:
        validation_prompt = f.read()
    
    return create_react_agent(
        model=ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=OPENAI_TEMPERATURE,
            max_tokens=OPENAI_MAX_TOKENS
        ),
        tools=[get_table_info],
        prompt=validation_prompt,
        name=VALIDATION_AGENT,
        response_format=ValidationOutput
    )


def create_reasoning_agent():
    """Create and return a Reasoning agent."""
    # Load reasoning prompt from file
    with open('prompts/reasoning_agent.txt', 'r') as f:
        reasoning_prompt = f.read()
    
    return create_react_agent(
        model=ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=OPENAI_TEMPERATURE,
            max_tokens=OPENAI_MAX_TOKENS
        ),
        tools=[],
        prompt=reasoning_prompt,
        name=REASONING_AGENT,
        response_format=ReasoningOutput
    )


def create_report_agent():
    """Create and return a Report agent."""
    # Load report prompt from file
    with open('prompts/report_agent.txt', 'r') as f:
        report_prompt = f.read()
    
    return create_react_agent(
        model=ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=OPENAI_TEMPERATURE,
            max_tokens=OPENAI_MAX_TOKENS
        ),
        tools=[save_report_to_markdown, complete_workflow],
        prompt=report_prompt,
        name=REPORT_AGENT,
        response_format=ReportOutput
    )




