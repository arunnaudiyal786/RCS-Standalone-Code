from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, START, END, MessagesState
from tools.ticket_tools import refine_query
from config.settings import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_MAX_TOKENS
from config.constants import INFO_RETRIEVER_AGENT, EXECUTION_AGENT, VALIDATION_AGENT, REASONING_AGENT, REPORT_AGENT, SUPERVISOR_AGENT
from graph.nodes import (
    query_refinement, query_refinement_check,
    ticket_refinement_step, reasoning_agent_node, report_agent_node,
    pii_guardrail_check, route_after_pii_check
)
from agents.specialized_agents import (
    create_info_retriever_agent, create_execution_agent,
    create_validation_agent, create_report_agent
)
from tools.handoff_tools import (
    assign_to_info_retriever, assign_to_execution,
    assign_to_validation, assign_to_report, complete_workflow
)
from utils.prompt_manager import get_prompt_manager


def create_supervisor_graph():
    """Create all worker agents and supervisor from scratch"""
    
    # Get prompt from PromptManager for supervisor
    prompt_manager = get_prompt_manager()
    supervisor_prompt_data = prompt_manager.get_prompt("supervisor-agent", label="production")

    # Get model configuration from prompt metadata with defaults
    model_config = supervisor_prompt_data.get_model_config({
        "model": OPENAI_MODEL,
        "temperature": OPENAI_TEMPERATURE,
        "max_tokens": OPENAI_MAX_TOKENS
    })

    # Initialize LLM with configuration from prompt
    llm = ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        model=model_config["model"],
        temperature=model_config["temperature"],
        max_tokens=model_config["max_tokens"]
    )

    # Create all worker agents
    info_retriever_agent = create_info_retriever_agent()
    execution_agent = create_execution_agent()
    validation_agent = create_validation_agent()
    report_agent = create_report_agent()

    # Create supervisor agent with handoff tools
    supervisor_agent = create_react_agent(
        model=llm,
        tools=[assign_to_info_retriever, assign_to_execution, assign_to_validation, assign_to_report, complete_workflow],
        prompt=supervisor_prompt_data.get_langchain_prompt(),
        name=SUPERVISOR_AGENT,
        # output_mode="full_history"
    )
    
    # Create multi-agent supervisor graph from scratch
    supervisor_graph = (
        StateGraph(MessagesState)
        .add_node("Input Guardrails", pii_guardrail_check)
        .add_node("Query Refinement Check", query_refinement_check)
        .add_node("Ticket Refinement Step", ticket_refinement_step)
        .add_node(REASONING_AGENT, reasoning_agent_node)
        .add_node(supervisor_agent, destinations=(INFO_RETRIEVER_AGENT, EXECUTION_AGENT, VALIDATION_AGENT, REPORT_AGENT, END))
        .add_node(info_retriever_agent)
        .add_node(execution_agent)
        .add_node(validation_agent)
        .add_node(REPORT_AGENT, report_agent_node)
        .add_edge(START, "Input Guardrails")
        .add_conditional_edges("Input Guardrails", route_after_pii_check)
        .add_conditional_edges("Query Refinement Check", query_refinement)
        .add_edge("Ticket Refinement Step", REASONING_AGENT)
        .add_edge(REASONING_AGENT, SUPERVISOR_AGENT)
        # Return to supervisor except for report agent
        .add_edge(INFO_RETRIEVER_AGENT, SUPERVISOR_AGENT)
        .add_edge(EXECUTION_AGENT, SUPERVISOR_AGENT)
        .add_edge(VALIDATION_AGENT, SUPERVISOR_AGENT)
        .add_edge(REPORT_AGENT, END)
        .compile()
    )
    
    return supervisor_graph