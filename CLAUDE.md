# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RCS-Standalone-Code is an Agentic RAG Ticket Resolution System built with LangChain, LangGraph, and OpenAI's GPT models. It implements a multi-agent architecture for intelligent ticket resolution with human-in-the-loop capabilities.

## Development Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Environment setup - create .env file with:
OPENAI_API_KEY=your_actual_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini  # optional
OPENAI_TEMPERATURE=0.1    # optional
OPENAI_MAX_TOKENS=4000    # optional
```

### Running the Application
```bash
# Main application entry point
python main.py

# Alternative entry point with more features
python standalone.py
```

### Development Environment
- Always use the `.venv` environment in the root directory for terminal tasks
- Ask for user permission before creating new files

## Architecture Overview

### Multi-Agent System Structure
The system uses a hierarchical multi-agent architecture with:

1. **Main Supervisor Graph** (`graph/supervisor_graph.py`):
   - Orchestrates the entire ticket resolution workflow
   - Manages state transitions between different processing stages

2. **Specialized Agents** (`agents/specialized_agents.py`):
   - **Reasoning Agent**: Analyzes and reasons about tickets
   - **Domain Supervisor Agent**: Coordinates info retrieval, execution, and validation
   - **Information Retrieval Agent**: Retrieves similar historical tickets from vector store
   - **Execution Agent**: Implements resolution steps
   - **Validation Agent**: Verifies resolution success with confidence scores
   - **Report Agent**: Generates final resolution reports

3. **Processing Pipeline**:
   - Query Refinement Check → Label Analysis → Pattern Analysis
   - Reasoning Agent → Domain Supervisor → Specialized Agents → Report

### Key Components

- **Vector Store Integration** (`utils/vector_store.py`): FAISS-based similarity search for historical tickets
- **Data Models** (`models/data_models.py`): Pydantic models for state management
- **Tools System**: 
  - `tools/ticket_tools.py`: Core ticket processing functions
  - `tools/handoff_tools.py`: Agent coordination and handoff mechanisms
- **Configuration** (`config/`): Environment settings and constants management

### State Management
Uses LangGraph's StateGraph with MessagesState for maintaining conversation context and workflow state across all agents.

## Development Guidelines

### Code Style
- Keep code crisp and concise
- Avoid unnecessary complexity
- Use modern Python practices with type hints
- Follow modular design patterns established in the codebase

### Agent Development
- Each agent is created using `create_react_agent` with specific tools and prompts
- Agents should have focused responsibilities (single purpose)
- Use proper error handling in agent implementations
- Maintain clear separation between reasoning, execution, and validation

### Configuration Management
All OpenAI settings are centralized in `config/settings.py` and loaded from environment variables with sensible defaults.