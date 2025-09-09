# RCS-Standalone_Code

## Agentic RAG Ticket Resolution System

A standalone implementation of an intelligent ticket resolution system using LangChain, LangGraph, and OpenAI's GPT models with human-in-the-loop (HITL) capabilities.

## Features

- **Multi-Agent Architecture**: RAG, Planning, Info Retrieval, Execution, and Validation agents
- **Vector Similarity Search**: FAISS-based retrieval of similar historical tickets
- **Human-in-the-Loop**: Interactive approval at key decision points
- **Environment Configuration**: Secure API key management via .env files
- **Comprehensive Resolution**: End-to-end ticket processing with validation

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your OpenAI API key:
   ```bash
   OPENAI_API_KEY=your_actual_openai_api_key_here
   ```

3. Optionally customize other settings:
   ```bash
   OPENAI_MODEL=gpt-4o-mini
   OPENAI_TEMPERATURE=0.1
   OPENAI_MAX_TOKENS=4000
   ```

### 3. Run the Application

```bash
python standalone.py
```

## Usage

The system will process a sample ticket and guide you through the resolution process with human approval checkpoints.

## Architecture

- **RAG Agent**: Retrieves similar historical tickets
- **Planning Agent**: Creates detailed resolution steps
- **Domain Supervisor**: Coordinates info retrieval, execution, and validation
- **Main Supervisor**: Orchestrates the entire process

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | Your OpenAI API key |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | OpenAI model to use |
| `OPENAI_TEMPERATURE` | No | `0.1` | Model temperature (0.0-2.0) |
| `OPENAI_MAX_TOKENS` | No | `4000` | Maximum tokens per response |