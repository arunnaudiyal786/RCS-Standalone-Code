from langgraph.graph import StateGraph, START, END
from models.data_models import MessagesState
from tools.ticket_tools import refine_query
from config.constants import INFO_RETRIEVER_AGENT, EXECUTION_AGENT, VALIDATION_AGENT, REASONING_AGENT, REPORT_AGENT, SUPERVISOR_AGENT
from graph.nodes import pattern_analysis, label_analysis, query_refinement, query_refinement_check, ticket_refinement_step, reasoning_agent_node
from agents.specialized_agents import (
    create_reasoning_agent, create_supervisor_agent, create_info_retriever_agent, 
    create_execution_agent, create_validation_agent, create_report_agent
)


def create_supervisor_graph():
    # Define the multi-agent supervisor graph
    supervisor = (
        StateGraph(MessagesState)
        .add_node("Query Refinement Check", query_refinement_check)
        .add_node("Ticket Refinement Step", ticket_refinement_step)
        # .add_node("Pattern Analysis Step", pattern_analysis)
        # .add_node("Label Analysis Step", label_analysis)
        .add_node(REASONING_AGENT, reasoning_agent_node)
        .add_node(create_supervisor_agent(), destinations=(INFO_RETRIEVER_AGENT, EXECUTION_AGENT, VALIDATION_AGENT, REPORT_AGENT, END))
        .add_node(create_info_retriever_agent())
        .add_node(create_execution_agent())
        .add_node(create_validation_agent())
        .add_node(create_report_agent())
        .add_edge(START, "Query Refinement Check")
        .add_conditional_edges("Query Refinement Check", query_refinement)
        # .add_edge("Refine Query Step", "Label Analysis Step")
        # .add_edge("Label Analysis Step", "Pattern Analysis Step")
        # .add_edge("Pattern Analysis Step", "Reasoning Agent")
        .add_edge("Ticket Refinement Step", REASONING_AGENT)
        .add_edge(REASONING_AGENT, SUPERVISOR_AGENT)
        .add_edge(INFO_RETRIEVER_AGENT, SUPERVISOR_AGENT)
        .add_edge(EXECUTION_AGENT, SUPERVISOR_AGENT)
        .add_edge(VALIDATION_AGENT, SUPERVISOR_AGENT)
        .add_edge(REPORT_AGENT, END)
        .compile()
    )
    
    return supervisor