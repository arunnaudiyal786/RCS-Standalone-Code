#!/usr/bin/env python3
"""
Script to generate the project structure and blank files for the LangGraph multi-agent system
"""

import os
from pathlib import Path

def create_directory_structure():
    """Create the directory structure for the project"""
    
    # Define the directory structure
    directories = [
        "config",
        "models", 
        "tools",
        "agents",
        "graph",
        "utils",
        "data"
    ]
    
    # Create directories
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Create __init__.py files to make them Python packages
    init_files = [
        "__init__.py",
        "config/__init__.py",
        "models/__init__.py", 
        "tools/__init__.py",
        "agents/__init__.py",
        "graph/__init__.py",
        "utils/__init__.py",
        "data/__init__.py"
    ]
    
    for init_file in init_files:
        Path(init_file).touch()
        print(f"Created file: {init_file}")
    
    # Create main files
    main_files = [
        "config/settings.py",
        "config/constants.py",
        "models/data_models.py",
        "tools/ticket_tools.py", 
        "tools/handoff_tools.py",
        "agents/specialized_agents.py",
        "graph/supervisor_graph.py",
        "graph/nodes.py",
        "utils/helpers.py",
        "utils/vector_store.py",
        "main.py",
        "requirements.txt",
        ".env.example"
    ]
    
    for file_path in main_files:
        Path(file_path).touch()
        print(f"Created file: {file_path}")
    
    print("\nProject structure created successfully!")
    print("\nDirectory structure:")
    print("├── config/")
    print("│   ├── __init__.py") 
    print("│   ├── settings.py")
    print("│   └── constants.py")
    print("├── models/")
    print("│   ├── __init__.py")
    print("│   └── data_models.py")
    print("├── tools/")
    print("│   ├── __init__.py")
    print("│   ├── ticket_tools.py")
    print("│   └── handoff_tools.py")
    print("├── agents/")
    print("│   ├── __init__.py")
    print("│   └── specialized_agents.py")
    print("├── graph/")
    print("│   ├── __init__.py")
    print("│   ├── supervisor_graph.py")
    print("│   └── nodes.py")
    print("├── utils/")
    print("│   ├── __init__.py")
    print("│   ├── helpers.py")
    print("│   └── vector_store.py")
    print("├── data/")
    print("│   └── __init__.py")
    print("├── main.py")
    print("├── requirements.txt")
    print("└── .env.example")

if __name__ == "__main__":
    create_directory_structure()