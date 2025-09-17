# RCS-Standalone-Code

**Agentic RAG Ticket Resolution System**

An intelligent multi-agent system built with LangChain, LangGraph, and OpenAI's GPT models for automated ticket resolution with human-in-the-loop capabilities.

## 🎯 Overview

RCS-Standalone-Code implements a sophisticated hierarchical multi-agent architecture that processes support tickets through an intelligent workflow. The system analyzes tickets, retrieves relevant historical data, executes resolution steps, validates results, and generates comprehensive reports.

## 🏗️ Architecture

The system follows a **Multi-Agent Supervisor Pattern** with the following key components:

### Main Supervisor Graph
- **File**: `graph/supervisor_graph.py`
- **Function**: Orchestrates the entire ticket resolution workflow
- **Responsibility**: Manages state transitions and coordinates agent interactions

### Specialized Agents
Located in `agents/specialized_agents.py`:

1. **Reasoning Agent** - Analyzes and reasons about ticket content
2. **Domain Supervisor Agent** - Coordinates information retrieval, execution, and validation
3. **Information Retrieval Agent** - Searches historical tickets using vector similarity
4. **Execution Agent** - Implements resolution steps and database operations
5. **Validation Agent** - Verifies resolution success with confidence scoring
6. **Report Agent** - Generates final resolution reports and documentation

### Processing Pipeline
```
Input Ticket → Query Refinement → Label Analysis → Pattern Analysis 
            → Reasoning Agent → Domain Supervisor → Specialized Agents → Report
```

## 📁 Project Structure

```
RCS-Standalone-Code/
├── agents/                     # Agent implementations
│   ├── __init__.py
│   └── specialized_agents.py   # All specialized agent definitions
├── config/                     # Configuration management
│   ├── __init__.py
│   ├── constants.py           # Agent names and system constants
│   └── settings.py            # Environment variables and OpenAI settings
├── data/                      # Sample data and table information
│   ├── sample_ticket.json     # Example ticket for testing
│   ├── sample_tickets/        # Multiple sample tickets
│   ├── table_data/           # Database table data files
│   └── table_description/    # Schema descriptions for tables
├── graph/                     # LangGraph workflow definitions
│   ├── __init__.py
│   ├── nodes.py              # Graph node implementations
│   └── supervisor_graph.py   # Main supervisor graph creation
├── models/                    # Data models and schemas
│   ├── __init__.py
│   └── data_models.py        # Pydantic models for state management
├── prompts/                   # Agent prompts and instructions
│   ├── domain_supervisor.txt
│   ├── execution_agent.txt
│   ├── info_retriever_agent.txt
│   ├── reasoning_agent.txt
│   ├── report_agent.txt
│   ├── supervisor_agent.txt
│   └── validation_agent.txt
├── sessions/                  # Runtime session data
│   └── [timestamp_folders]/   # Session-specific outputs and logs
├── tools/                     # Agent tools and utilities
│   ├── __init__.py
│   ├── handoff_tools.py      # Agent coordination and handoff functions
│   ├── report_tools.py       # Report generation tools
│   └── ticket_tools.py       # Core ticket processing functions
├── utils/                     # Utility functions
│   ├── __init__.py
│   ├── helpers.py            # General helper functions
│   └── vector_store.py       # FAISS vector store for similarity search
├── main.py                    # Main application entry point
├── requirements.txt           # Python dependencies
├── CLAUDE.md                 # Development guidelines and project documentation
└── supervisor_graph.png      # Generated workflow visualization
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd RCS-Standalone-Code
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment setup**
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your_actual_openai_api_key_here
   OPENAI_MODEL=gpt-4o-mini
   OPENAI_TEMPERATURE=0.1
   OPENAI_MAX_TOKENS=4000
   ```

### Running the Application

**Main entry point:**
```bash
python main.py
```

This command will:
- Initialize the multi-agent supervisor graph
- Generate a workflow visualization (`supervisor_graph.png`)
- Process a sample ticket through the complete workflow
- Create session outputs in the `sessions/` directory

**Alternative entry point:**
```bash
python standalone.py
```

## 🔧 Key Components

### Configuration Management (`config/`)
- **`settings.py`**: Centralized OpenAI configuration loaded from environment variables
- **`constants.py`**: Agent names and system constants

### Data Models (`models/data_models.py`)
Pydantic models for type-safe state management:
- `QueryRefinementOutput`: Query processing results
- `InputTicket`: Immutable input ticket model
- `TicketRefinementOutput`: Refined ticket data
- `ReasoningOutput`: Reasoning agent results
- `ValidationResult`: Validation scores and feedback

### Vector Store Integration (`utils/vector_store.py`)
- **Technology**: FAISS-based similarity search
- **Purpose**: Retrieves relevant historical tickets
- **Embeddings**: OpenAI text-embedding-3-small model
- **Functionality**: Semantic search for ticket resolution patterns

### Tools System (`tools/`)
- **`ticket_tools.py`**: Core ticket processing, database operations, similarity search
- **`handoff_tools.py`**: Agent coordination and workflow handoffs
- **`report_tools.py`**: Report generation and formatting

### Graph Nodes (`graph/nodes.py`)
Implements the workflow steps:
- Query refinement and validation
- Ticket processing and enrichment
- Agent coordination nodes
- Report generation

## 🔄 Workflow Details

### Processing Stages

1. **Query Refinement Check** - Validates and refines input tickets
2. **Label Analysis** - Categorizes and labels ticket types
3. **Pattern Analysis** - Identifies resolution patterns
4. **Reasoning Agent** - Analyzes ticket context and requirements
5. **Domain Supervisor** - Coordinates specialized agent execution
6. **Information Retrieval** - Searches for similar historical tickets
7. **Execution** - Implements resolution steps and database operations
8. **Validation** - Verifies resolution success with confidence scoring
9. **Report Generation** - Creates comprehensive resolution documentation

### State Management
- **Technology**: LangGraph's StateGraph with MessagesState
- **Purpose**: Maintains conversation context across all agents
- **Persistence**: Session-based storage in `sessions/` directory

## 📊 Output and Sessions

Each execution creates a timestamped session folder containing:
- **Query refinement outputs** - Initial processing results
- **Reasoning agent outputs** - Analysis and reasoning logs
- **Report files** - Final resolution reports in Markdown format
- **Agent-specific logs** - Detailed execution traces

Session format: `sessions/MMDDYYYY_HHMM_[id]/`

## 🛠️ Development Guidelines

### Code Style
- Modern Python with type hints
- Modular design following established patterns
- Focused agent responsibilities (single purpose)
- Comprehensive error handling

### Agent Development
- Agents created using `create_react_agent` pattern
- Specific tools and prompts for each agent
- Clear separation between reasoning, execution, and validation
- Proper state management across agent interactions

### Adding New Agents
1. Define agent in `agents/specialized_agents.py`
2. Create corresponding prompt in `prompts/`
3. Add agent constant in `config/constants.py`
4. Integrate into supervisor graph workflow
5. Add necessary tools and handoff functions

## 🧪 Testing

The system includes sample tickets for testing:
- `data/sample_ticket.json` - Primary test ticket
- `data/sample_tickets/` - Multiple scenario examples
- Each ticket tests different resolution patterns

## 📝 Dependencies

### Core Dependencies
- **langchain** - LLM framework and tools
- **langgraph** - Graph-based workflow orchestration
- **langchain-openai** - OpenAI integration
- **faiss-cpu** - Vector similarity search
- **pydantic** - Data validation and serialization

### Additional Dependencies
- **python-dotenv** - Environment variable management
- **chromadb** - Alternative vector database support
- **typing-extensions** - Enhanced type annotations

## 🔐 Security & Configuration

- API keys managed through environment variables
- No hardcoded credentials in source code
- Secure configuration patterns in `config/settings.py`
- Session data isolated in timestamped directories

## 📈 Monitoring & Logging

- Comprehensive session logging in `sessions/` directory
- Graph visualization generation (`supervisor_graph.png`)
- Agent-specific output tracking
- Execution flow monitoring through LangGraph

## 🤝 Contributing

1. Follow the established code patterns in the codebase
2. Maintain modular agent architecture
3. Add appropriate error handling and logging
4. Update documentation for new features
5. Test with sample tickets before deployment

## 📄 License

This project is part of a larger enterprise solution for intelligent ticket resolution systems.

---

For detailed development guidelines and agent implementation patterns, see `CLAUDE.md`.