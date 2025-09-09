#!/usr/bin/env python3
"""
Main entry point for the LangGraph multi-agent system
"""

import subprocess
from graph.supervisor_graph import create_supervisor_graph
from utils.helpers import pretty_print_messages


def main():
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

    # Example usage (you can extend this)
    print("\nMulti-agent system initialized successfully!")
    print("You can now use the supervisor graph to process tickets.")


if __name__ == "__main__":
    main()