#!/usr/bin/env python3
"""
Main entry point for the LangGraph multi-agent system
"""

import subprocess
from graph.supervisor_graph import create_supervisor_graph
from utils.helpers import pretty_print_messages


def main(ticket_input: str = None):
    # Create the supervisor graph
    supervisor = create_supervisor_graph()
    
    # Save the graph image to a file
    graph_image = supervisor.get_graph().draw_mermaid_png()
    with open("supervisor_graph.png", "wb") as f:
        f.write(graph_image)

    print("Graph saved as 'supervisor_graph.png'")

    # Optionally open it automatically (macOS)
    try:
        subprocess.run(["open", "supervisor_graph.png"])
    except FileNotFoundError:
        print("Could not open graph automatically. Please view supervisor_graph.png manually.")

    # Example usage - actually run the workflow
    print("\nMulti-agent system initialized successfully!")
    
    # Use provided ticket input or default message
    if ticket_input:
        message_content = f"Process this ticket: {ticket_input}"
        print(f"Processing provided ticket: {ticket_input}")
    else:
        message_content = "Process the sample ticket"
        print("Processing sample ticket...")
    
    # Run the workflow with ticket input
    try:
        for chunk in supervisor.stream(
            {"messages": [{"role": "user", "content": message_content}]},
            config={"configurable": {"thread_id": "test_session_1"}, "recursion_limit": 50}
        ):
            pretty_print_messages(chunk)
            
        print("\nWorkflow execution completed. Check the sessions folder for output files.")
        
    except Exception as e:
        print(f"Error running workflow: {e}")
        print("Graph visualization completed successfully.")


if __name__ == "__main__":
    main()