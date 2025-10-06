from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from config.settings import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_MAX_TOKENS
from config.constants import INFO_RETRIEVER_AGENT, EXECUTION_AGENT, VALIDATION_AGENT, REASONING_AGENT, REPORT_AGENT
from tools.ticket_tools import retrieve_similar_tickets, validate_resolution, retrieve_table_schema_info, get_table_info, insert_row_to_text_file, update_value_in_text_file, get_table_desc
from tools.handoff_tools import complete_workflow
from tools.report_tools import save_report_to_markdown
from models.data_models import ReasoningOutput, InfoRetrieverOutput, ExecutionOutput, ValidationOutput, ReportOutput
from utils.prompt_manager import get_prompt_manager


def create_info_retriever_agent():
    """Create and return an Information Retrieval agent."""
    # Get prompt from PromptManager with fallback to local file
    prompt_manager = get_prompt_manager()
    prompt_data = prompt_manager.get_prompt("info-retriever-agent", label="production")

    # Get model configuration from prompt metadata with defaults
    model_config = prompt_data.get_model_config({
        "model": OPENAI_MODEL,
        "temperature": OPENAI_TEMPERATURE,
        "max_tokens": OPENAI_MAX_TOKENS
    })

    return create_react_agent(
        model=ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model=model_config["model"],
            temperature=model_config["temperature"],
            max_tokens=model_config["max_tokens"]
        ),
        tools=[retrieve_similar_tickets, retrieve_table_schema_info, get_table_info, get_table_desc],
        prompt=prompt_data.get_langchain_prompt(),
        name=INFO_RETRIEVER_AGENT,
        response_format=InfoRetrieverOutput
    )


def create_execution_agent():
    """Create and return an Execution agent."""
    # Get prompt from PromptManager with fallback to local file
    prompt_manager = get_prompt_manager()
    prompt_data = prompt_manager.get_prompt("execution-agent", label="production")

    # Get model configuration from prompt metadata with defaults
    model_config = prompt_data.get_model_config({
        "model": OPENAI_MODEL,
        "temperature": OPENAI_TEMPERATURE,
        "max_tokens": OPENAI_MAX_TOKENS
    })

    return create_react_agent(
        model=ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model=model_config["model"],
            temperature=model_config["temperature"],
            max_tokens=model_config["max_tokens"]
        ),
        tools=[insert_row_to_text_file, update_value_in_text_file],
        prompt=prompt_data.get_langchain_prompt(),
        name=EXECUTION_AGENT
    )


def create_validation_agent():
    """Create and return a Validation agent."""
    # Get prompt from PromptManager with fallback to local file
    prompt_manager = get_prompt_manager()
    prompt_data = prompt_manager.get_prompt("validation-agent", label="production")

    # Get model configuration from prompt metadata with defaults
    model_config = prompt_data.get_model_config({
        "model": OPENAI_MODEL,
        "temperature": OPENAI_TEMPERATURE,
        "max_tokens": OPENAI_MAX_TOKENS
    })

    return create_react_agent(
        model=ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model=model_config["model"],
            temperature=model_config["temperature"],
            max_tokens=model_config["max_tokens"]
        ),
        tools=[get_table_info],
        prompt=prompt_data.get_langchain_prompt(),
        name=VALIDATION_AGENT,
        response_format=ValidationOutput
    )


def create_reasoning_agent():
    """Create and return a Reasoning agent."""
    # Get prompt from PromptManager with fallback to local file
    prompt_manager = get_prompt_manager()
    prompt_data = prompt_manager.get_prompt("reasoning-agent", label="production")

    # Get model configuration from prompt metadata with defaults
    model_config = prompt_data.get_model_config({
        "model": OPENAI_MODEL,
        "temperature": OPENAI_TEMPERATURE,
        "max_tokens": OPENAI_MAX_TOKENS
    })

    return create_react_agent(
        model=ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model=model_config["model"],
            temperature=model_config["temperature"],
            max_tokens=model_config["max_tokens"]
        ),
        tools=[],
        prompt=prompt_data.get_langchain_prompt(),
        name=REASONING_AGENT,
        response_format=ReasoningOutput
    )


def create_report_agent():
    """Create and return a Report agent."""
    # Get prompt from PromptManager with fallback to local file
    prompt_manager = get_prompt_manager()
    prompt_data = prompt_manager.get_prompt("report-agent", label="production")

    # Get model configuration from prompt metadata with defaults
    model_config = prompt_data.get_model_config({
        "model": OPENAI_MODEL,
        "temperature": OPENAI_TEMPERATURE,
        "max_tokens": OPENAI_MAX_TOKENS
    })

    return create_react_agent(
        model=ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model=model_config["model"],
            temperature=model_config["temperature"],
            max_tokens=model_config["max_tokens"]
        ),
        tools=[save_report_to_markdown, complete_workflow],
        prompt=prompt_data.get_langchain_prompt(),
        name=REPORT_AGENT,
        response_format=ReportOutput
    )




