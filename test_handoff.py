#!/usr/bin/env python3
import sys
sys.path.append('.')
from graph.supervisor_graph import create_supervisor_graph

# Create the supervisor graph
supervisor = create_supervisor_graph()

# Run a test to see exactly when the error occurs
try:
    count = 0
    for result in supervisor.stream(
        {'messages': [{'role': 'user', 'content': 'test ticket'}]}, 
        config={'recursion_limit': 20}
    ):
        count += 1
        print(f"\n=== Step {count} ===")
        for node_name, node_data in result.items():
            print(f"Node: {node_name}")
            if 'messages' in node_data and node_data['messages']:
                last_message = node_data['messages'][-1]
                if hasattr(last_message, 'content'):
                    content = last_message.content[:200] + "..." if len(last_message.content) > 200 else last_message.content
                    print(f"  Content: {content}")
                if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                    print(f"  Tool calls: {[tc.get('name', 'unknown') for tc in last_message.tool_calls]}")
        
        if count > 15:  # Prevent infinite loop
            break
            
except Exception as e:
    print(f"\nError occurred: {e}")
    import traceback
    traceback.print_exc()