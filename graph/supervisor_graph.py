from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, START, END, MessagesState
from tools.ticket_tools import refine_query
from config.settings import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_MAX_TOKENS
from config.constants import INFO_RETRIEVER_AGENT, EXECUTION_AGENT, VALIDATION_AGENT, REASONING_AGENT, REPORT_AGENT, SUPERVISOR_AGENT
from graph.nodes import (
    query_refinement, query_refinement_check, 
    ticket_refinement_step, reasoning_agent_node, report_agent_node
)
from agents.specialized_agents import (
    create_info_retriever_agent, create_execution_agent, 
    create_validation_agent, create_report_agent
)
from tools.handoff_tools import (
    assign_to_info_retriever, assign_to_execution, 
    assign_to_validation, assign_to_report, complete_workflow
)


def create_supervisor_graph():
    """Create all worker agents and supervisor from scratch"""
    
    # Initialize LLM
    llm = ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=OPENAI_TEMPERATURE,
        max_tokens=OPENAI_MAX_TOKENS
    )
    
    # Create all worker agents
    info_retriever_agent = create_info_retriever_agent()
    execution_agent = create_execution_agent()
    validation_agent = create_validation_agent()
    report_agent = create_report_agent()
    
    # Load supervisor prompt from file
    with open('prompts/supervisor_agent.txt', 'r') as f:
        supervisor_prompt = f.read()
    
    # Create supervisor agent with handoff tools
    supervisor_agent = create_react_agent(
        model=llm,
        tools=[assign_to_info_retriever, assign_to_execution, assign_to_validation, assign_to_report, complete_workflow],
        prompt=supervisor_prompt,
        name=SUPERVISOR_AGENT
    )
    
    # Create multi-agent supervisor graph from scratch
    supervisor_graph = (
        StateGraph(MessagesState)
        .add_node("Query Refinement Check", query_refinement_check)
        .add_node("Ticket Refinement Step", ticket_refinement_step)
        .add_node(REASONING_AGENT, reasoning_agent_node)
        .add_node(supervisor_agent, destinations=(INFO_RETRIEVER_AGENT, EXECUTION_AGENT, VALIDATION_AGENT, REPORT_AGENT, END))
        .add_node(info_retriever_agent)
        .add_node(execution_agent)
        .add_node(validation_agent)
        .add_node(REPORT_AGENT, report_agent_node)
        .add_edge(START, "Query Refinement Check")
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