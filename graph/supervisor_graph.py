from langgraph.graph import StateGraph, START, END
from models.data_models import MessagesState
from tools.ticket_tools import refine_query
from graph.nodes import pattern_analysis, label_analysis, query_refinement
from agents.specialized_agents import (
    reasoning_agent, supervisor_agent, info_retriever, 
    execution_agent, validation_agent, report_agent
)


def create_supervisor_graph():
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
        .add_conditional_edges("Query Refinement Check", query_refinement)
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
    
    return supervisor