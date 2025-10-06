# Langfuse Integration Documentation

## Table of Contents

1. [Overview](#overview)
2. [Why Langfuse?](#why-langfuse)
3. [Features Implemented](#features-implemented)
4. [Architecture](#architecture)
5. [Configuration](#configuration)
6. [Feature 1: LLM Observability & Tracing](#feature-1-llm-observability--tracing)
7. [Feature 2: Centralized Prompt Management](#feature-2-centralized-prompt-management)
8. [Feature 3: Prompt Synchronization](#feature-3-prompt-synchronization)
9. [Code Locations Reference](#code-locations-reference)
10. [Setup Guide](#setup-guide)
11. [Usage Examples](#usage-examples)
12. [Troubleshooting](#troubleshooting)
13. [Best Practices](#best-practices)

---

## Overview

This project integrates **Langfuse**, an open-source LLM engineering platform, to provide comprehensive observability, prompt management, and team collaboration capabilities for the multi-agent ticket resolution system.

**Langfuse** is a production-ready platform for:
- **Observability**: Track and analyze LLM calls, token usage, latency, and costs
- **Prompt Management**: Version control, A/B testing, and centralized prompt storage
- **Collaboration**: Enable teams to work together on prompts and monitor production systems

### Integration Status

✅ **Fully Integrated** - All three major Langfuse features are implemented:
1. LLM observability and distributed tracing
2. Centralized prompt management with versioning
3. Bidirectional prompt synchronization

🔧 **Configurable** - All features can be enabled/disabled via environment variables

🔒 **Fallback-Safe** - System continues to work even if Langfuse is unavailable

---

## Why Langfuse?

### Problems Solved

1. **Lack of Observability**
   - **Problem**: Hard to debug multi-agent workflows, understand token costs, identify bottlenecks
   - **Solution**: Langfuse traces every LLM call with full context, session correlation, and performance metrics

2. **Prompt Version Control**
   - **Problem**: Prompts scattered across local files, no version history, difficult to A/B test
   - **Solution**: Centralized prompt storage with automatic versioning, labels, and model configurations

3. **Team Collaboration Challenges**
   - **Problem**: Multiple developers editing prompts locally leads to conflicts and inconsistencies
   - **Solution**: Bidirectional sync with conflict detection, enabling UI-based prompt editing

4. **Production Monitoring**
   - **Problem**: No visibility into production LLM behavior, costs, or failures
   - **Solution**: Real-time monitoring dashboards, error tracking, and performance analytics

5. **Prompt Engineering Workflow**
   - **Problem**: Testing prompt changes requires code deployment
   - **Solution**: Hot-reload prompts from Langfuse without restarting the application

### Benefits in This Project

- 📊 **Session-Correlated Tracing**: Each ticket resolution session is tracked end-to-end across all agents
- 🔄 **Dynamic Prompt Loading**: Prompts are fetched from Langfuse at runtime with local fallback
- 👥 **Team Collaboration**: Multiple team members can edit prompts via Langfuse UI
- 📈 **Cost Tracking**: Monitor token usage and costs per agent and per session
- 🐛 **Debugging**: Inspect full conversation history, tool calls, and agent decisions
- 🚀 **Rapid Iteration**: Update prompts in production without code changes

---

## Features Implemented

### 1. LLM Observability & Tracing ✅

**Status**: Fully Implemented

**Capabilities**:
- ✅ Automatic tracing of all LLM calls via LangChain CallbackHandler
- ✅ Session correlation (local session IDs linked to Langfuse traces)
- ✅ Multi-agent workflow tracking across reasoning, execution, validation, and reporting
- ✅ Token usage and cost tracking per agent
- ✅ Latency metrics for each LLM call
- ✅ Prompt version metadata attached to traces
- ✅ Error tracking and debugging

**Use Cases**:
- Debug why an agent made a specific decision
- Analyze performance bottlenecks in the workflow
- Track token costs per ticket type
- Monitor production system health

### 2. Centralized Prompt Management ✅

**Status**: Fully Implemented

**Capabilities**:
- ✅ `PromptManager` singleton for centralized prompt access
- ✅ Fetch prompts from Langfuse by name and label (production, staging, etc.)
- ✅ Model configuration stored with prompts (model, temperature, max_tokens)
- ✅ Intelligent caching with configurable TTL (default: 300 seconds)
- ✅ Automatic fallback to local files if Langfuse is unavailable
- ✅ Version-aware prompt fetching
- ✅ Integration with all agents and workflow nodes

**Use Cases**:
- Update prompts without redeploying code
- A/B test different prompt versions
- Rollback to previous prompt versions
- Manage prompts across environments (dev, staging, production)

### 3. Bidirectional Prompt Synchronization ✅

**Status**: Fully Implemented

**Capabilities**:
- ✅ Pull prompts from Langfuse to local files
- ✅ Push local prompts to Langfuse
- ✅ Checksum-based change detection
- ✅ Conflict detection when both local and remote change
- ✅ Conflict resolution strategies (keep local or remote)
- ✅ Metadata tracking with JSON persistence
- ✅ CLI tool for sync operations
- ✅ Migration script for initial upload

**Use Cases**:
- Sync prompts edited in Langfuse UI to local development
- Push locally-developed prompts to Langfuse
- Resolve conflicts when multiple team members edit prompts
- Track sync history and status

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Ticket Resolution System                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Reasoning   │  │  Execution   │  │  Validation  │          │
│  │    Agent     │  │    Agent     │  │    Agent     │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                   │
│         └──────────────────┴──────────────────┘                  │
│                            │                                      │
│                            ▼                                      │
│              ┌─────────────────────────┐                         │
│              │   PromptManager         │                         │
│              │  (Singleton Pattern)    │                         │
│              └──────────┬──────────────┘                         │
│                         │                                         │
│         ┌───────────────┴───────────────┐                        │
│         │                               │                         │
│         ▼                               ▼                         │
│  ��─────────────┐                ┌─────────────┐                 │
│  │  Langfuse   │                │   Local     │                 │
│  │  (Cloud/    │◄───sync───────►│   Files     │                 │
│  │  Self-Host) │                │  (prompts/) │                 │
│  └─────────────┘                └─────────────┘                 │
│         │                                                         │
│         │ (Tracing Callbacks)                                    │
│         ▼                                                         │
│  ┌─────────────────────────────┐                                │
│  │  Langfuse Dashboard         │                                │
│  │  - Traces                   │                                │
│  │  - Analytics                │                                │
│  │  - Prompt Versions          │                                │
│  └─────────────────────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

#### Tracing Flow
```
User Request → main.py → Supervisor Graph
                  ↓
          get_langfuse_handler()
                  ↓
      CallbackHandler attached to config
                  ↓
    Agents execute (reasoning, validation, etc.)
                  ↓
    LLM calls automatically traced to Langfuse
                  ↓
         Traces viewable in Langfuse UI
```

#### Prompt Management Flow
```
Agent Initialization
        ↓
  PromptManager.get_prompt("agent-name")
        ↓
   Check cache (TTL-based)
        ↓
   Cache miss?
        ├─ Yes → Fetch from Langfuse
        │         ├─ Success → Cache + Return
        │         └─ Fail → Fallback to local file
        └─ No → Return cached prompt
```

#### Synchronization Flow
```
Developer edits prompt in Langfuse UI
        ↓
Run: python scripts/sync_prompts.py status
        ↓
   Status shows "Modified remotely"
        ↓
Run: python scripts/sync_prompts.py pull
        ↓
   Local file updated with remote version
        ↓
   Metadata updated with new checksum
```

---

## Configuration

### Environment Variables

All Langfuse features are controlled via environment variables in `.env`:

#### Core Configuration

```bash
# Master switch - enables/disables all Langfuse features
LANGFUSE_ENABLED=true

# Langfuse credentials (required if enabled)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...

# Langfuse host URL
# Use cloud: https://cloud.langfuse.com
# Or self-hosted: http://localhost:3000
LANGFUSE_HOST=https://cloud.langfuse.com
```

#### Prompt Management Configuration

```bash
# Enable centralized prompt management
LANGFUSE_PROMPT_MANAGEMENT_ENABLED=true

# Fallback to local files if Langfuse unavailable
LANGFUSE_PROMPT_FALLBACK_TO_LOCAL=true

# Prompt cache TTL in seconds (default: 300 = 5 minutes)
LANGFUSE_PROMPT_CACHE_TTL=300
```

#### Prompt Sync Configuration

```bash
# Metadata file location for sync tracking
LANGFUSE_PROMPT_SYNC_METADATA_FILE=prompts/.prompt_metadata.json

# Auto-resolve conflicts (not recommended for production)
LANGFUSE_PROMPT_SYNC_AUTO_RESOLVE=false

# Default label for prompt fetching
LANGFUSE_PROMPT_SYNC_DEFAULT_LABEL=production
```

### Configuration Matrix

| Feature | Required Variables | Optional Variables |
|---------|-------------------|-------------------|
| **Observability/Tracing** | `LANGFUSE_ENABLED=true`<br>`LANGFUSE_PUBLIC_KEY`<br>`LANGFUSE_SECRET_KEY` | `LANGFUSE_HOST` |
| **Prompt Management** | Same as above +<br>`LANGFUSE_PROMPT_MANAGEMENT_ENABLED=true` | `LANGFUSE_PROMPT_FALLBACK_TO_LOCAL`<br>`LANGFUSE_PROMPT_CACHE_TTL` |
| **Prompt Sync** | Same as Prompt Management | `LANGFUSE_PROMPT_SYNC_METADATA_FILE`<br>`LANGFUSE_PROMPT_SYNC_AUTO_RESOLVE`<br>`LANGFUSE_PROMPT_SYNC_DEFAULT_LABEL` |

### Feature Flags

You can mix and match features:

```bash
# Scenario 1: Only Tracing (no prompt management)
LANGFUSE_ENABLED=true
LANGFUSE_PROMPT_MANAGEMENT_ENABLED=false

# Scenario 2: Prompt Management with local fallback (no tracing)
LANGFUSE_ENABLED=true
LANGFUSE_PROMPT_MANAGEMENT_ENABLED=true
# Don't pass callbacks to agents (modify code)

# Scenario 3: Everything disabled (pure local mode)
LANGFUSE_ENABLED=false
```

---

## Feature 1: LLM Observability & Tracing

### Overview

Langfuse tracing provides end-to-end visibility into multi-agent workflows, tracking every LLM call, tool invocation, and agent decision.

### How It Works

1. **Initialization** ([main.py:42-71](../main.py#L42-L71))
   - `get_langfuse_handler()` creates a CallbackHandler instance
   - Handler is attached to LangGraph config
   - Session ID correlates local session with Langfuse traces
   - Prompt version metadata is attached to traces

2. **Agent-Level Tracing** ([graph/nodes.py:320-334](../graph/nodes.py#L320-L334), [408-488](../graph/nodes.py#L408-L488))
   - Each agent node creates a session-specific handler
   - Trace name includes session ID for easy filtering
   - All LLM calls within the agent are automatically traced

3. **Data Captured**
   - Input prompts and messages
   - LLM responses
   - Token counts (prompt, completion, total)
   - Latency for each call
   - Model configuration (temperature, max_tokens)
   - Error traces if calls fail
   - Tool calls and results (for ReAct agents)

### Code Implementation

#### Main Workflow Tracing

**File**: [main.py:42-71](../main.py#L42-L71)

```python
# Create LangFuse handler with session correlation
langfuse_handler = get_langfuse_handler(
    session_id="test_session_1",
    trace_name="supervisor_workflow_execution"
)

# Build config with LangFuse callbacks
config = {
    "configurable": {"thread_id": "test_session_1"},
    "recursion_limit": 50
}

# Add callbacks and prompt version tracking metadata
if langfuse_handler:
    config["callbacks"] = [langfuse_handler]
    config["metadata"] = {
        "prompt_versions": {
            "reasoning_agent": "production",
            "supervisor_agent": "production",
            # ... other agents
        },
        "prompt_management_enabled": True
    }
```

#### Reasoning Agent Tracing

**File**: [graph/nodes.py:320-334](../graph/nodes.py#L320-L334)

```python
# Get LangFuse handler with session correlation
langfuse_handler = get_langfuse_handler(
    session_id=session_id,
    trace_name=f"reasoning_agent_{session_id}"
)

# Build config with callbacks
config = {}
if langfuse_handler:
    config["callbacks"] = [langfuse_handler]

# Get response from reasoning agent with tracing
response = reasoning_agent.invoke(
    {"messages": [HumanMessage(content=input_message)]},
    config=config
)
```

### What Gets Traced

| Component | Information Captured |
|-----------|---------------------|
| **LLM Calls** | Model name, temperature, max_tokens, input prompt, output text, token counts, latency |
| **Agent Executions** | Agent name, input state, output state, tool calls, execution time |
| **Tool Calls** | Tool name, input parameters, output results, success/failure status |
| **Sessions** | Session ID, ticket ID, timestamp, workflow path taken |
| **Errors** | Exception traces, failed LLM calls, tool failures |

### Viewing Traces

1. **Access Langfuse Dashboard**: Navigate to your Langfuse instance
2. **Filter by Session**: Use session_id to find specific ticket resolutions
3. **Inspect Traces**: Click on a trace to see full conversation history
4. **Analyze Costs**: View token usage and estimated costs
5. **Debug Issues**: See exact prompts, responses, and errors

### Session Correlation

Each ticket resolution creates a unique session ID (format: `MMDDYYYY_HHMM_UUID`):

```python
# Example session IDs
"10032025_2027_fd94"
"10042025_1814_c280"
```

This session ID is:
- Used as the local folder name in `sessions/`
- Passed to Langfuse as `session_id` parameter
- Used in trace names for easy filtering
- Correlates all agents in the workflow

---

## Feature 2: Centralized Prompt Management

### Overview

The `PromptManager` provides a centralized way to fetch prompts from Langfuse with intelligent caching and local fallback.

### How It Works

1. **Singleton Pattern** - Single global instance manages all prompts
2. **Cache-First** - Checks cache before fetching from Langfuse
3. **Fallback-Safe** - Falls back to local files if Langfuse unavailable
4. **Model Configuration** - Prompts include model settings (temperature, max_tokens)
5. **Version/Label Support** - Fetch specific versions or labels (production, staging)

### Architecture

**File**: [utils/prompt_manager.py](../utils/prompt_manager.py)

```
┌─────────────────────────────────────────────────┐
│              PromptManager                       │
│                (Singleton)                       │
├─────────────────────────────────────────────────┤
│  Cache (TTL-based)                              │
│  ┌────────────────────────────────────┐         │
│  │ "reasoning-agent:production:None"  │         │
│  │ → (PromptData, timestamp)          │         │
│  └────────────────────────────────────┘         │
├─────────────────────────────────────────────────┤
│  get_prompt(name, label, version)               │
│    ├─ Check cache                               │
│    ├─ Fetch from Langfuse (if enabled)          │
│    └─ Fallback to local file                    │
└─────────────────────────────────────────────────┘
```

### Code Implementation

#### PromptManager Class

**File**: [utils/prompt_manager.py:53-206](../utils/prompt_manager.py#L53-L206)

```python
class PromptManager:
    """
    Centralized prompt management with Langfuse integration

    Features:
    - Fetches prompts from Langfuse with version/label support
    - Caches prompts to reduce API calls
    - Falls back to local files if Langfuse unavailable
    - Thread-safe singleton pattern
    """

    def get_prompt(self, name: str, label: str = "production", version: Optional[int] = None) -> PromptData:
        # Check cache
        if cache_key in self._cache:
            cached_prompt, cached_time = self._cache[cache_key]
            if datetime.now() - cached_time < timedelta(seconds=LANGFUSE_PROMPT_CACHE_TTL):
                return cached_prompt

        # Try Langfuse first
        if self._langfuse_client and LANGFUSE_PROMPT_MANAGEMENT_ENABLED:
            try:
                prompt_data = self._fetch_from_langfuse(name, label, version)
                self._cache[cache_key] = (prompt_data, datetime.now())
                return prompt_data
            except Exception:
                # Fallback to local
                pass

        # Fallback to local file
        return self._fetch_from_local(name)
```

#### Usage in Agents

**File**: [agents/specialized_agents.py:14-36](../agents/specialized_agents.py#L14-L36)

```python
def create_info_retriever_agent():
    # Get prompt from PromptManager
    prompt_manager = get_prompt_manager()
    prompt_data = prompt_manager.get_prompt("info-retriever-agent", label="production")

    # Extract model configuration from prompt metadata
    model_config = prompt_data.get_model_config({
        "model": OPENAI_MODEL,
        "temperature": OPENAI_TEMPERATURE,
        "max_tokens": OPENAI_MAX_TOKENS
    })

    # Create agent with dynamic configuration
    return create_react_agent(
        model=ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model=model_config["model"],
            temperature=model_config["temperature"],
            max_tokens=model_config["max_tokens"]
        ),
        tools=[...],
        prompt=prompt_data.get_langchain_prompt(),
        name=INFO_RETRIEVER_AGENT,
        response_format=InfoRetrieverOutput
    )
```

#### Usage in Workflow Nodes

**File**: [graph/nodes.py:101-119](../graph/nodes.py#L101-L119)

```python
def query_refinement_check(state: SolutionState):
    # Get prompt from PromptManager
    prompt_manager = get_prompt_manager()
    prompt_data = prompt_manager.get_prompt("query-refinement-check-with-refined", label="production")

    # Extract model config from prompt metadata
    model_config = prompt_data.get_model_config({
        "model": OPENAI_MODEL,
        "temperature": OPENAI_TEMPERATURE,
        "max_tokens": OPENAI_MAX_TOKENS
    })

    # Create LLM with configuration from prompt
    llm = ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        model=model_config["model"],
        temperature=model_config["temperature"],
        max_tokens=model_config["max_tokens"]
    )

    prompt_template = prompt_data.get_langchain_prompt()
    # ... use prompt
```

### Prompt Name Mapping

Local files use **snake_case**, Langfuse uses **kebab-case**:

| Local File | Langfuse Name |
|------------|---------------|
| `reasoning_agent.txt` | `reasoning-agent` |
| `info_retriever_agent.txt` | `info-retriever-agent` |
| `execution_agent.txt` | `execution-agent` |
| `validation_agent.txt` | `validation-agent` |
| `supervisor_agent.txt` | `supervisor-agent` |
| `report_agent.txt` | `report-agent` |
| `query_refinement_check.txt` | `query-refinement-check` |
| `ticket_refinement.txt` | `ticket-refinement` |
| `query_refinement_check_with_refined.txt` | `query-refinement-check-with-refined` |

**File**: [utils/prompt_sync.py:25-40](../utils/prompt_sync.py#L25-L40)

### Cache Behavior

- **Cache Key Format**: `{name}:{label}:{version}`
- **TTL**: Configurable via `LANGFUSE_PROMPT_CACHE_TTL` (default: 300 seconds)
- **Cache Invalidation**: Automatic after TTL expires
- **Manual Clear**: `PromptManager().clear_cache()`

### Fallback Mechanism

```
┌─────────────────────────────────────────────┐
│  Agent requests prompt "reasoning-agent"    │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│  Check cache (TTL-based)                    │
└────┬──────────────────────────────────┬─────┘
     │ Hit                               │ Miss
     ▼                                   ▼
┌─────────────┐              ┌───────────────────────┐
│ Return      │              │ Langfuse enabled?     │
│ cached      │              └───┬─────────────┬─────┘
│ prompt      │                  │ Yes         │ No
└─────────────┘                  ▼             ▼
                      ┌───────────────┐  ┌──────────────┐
                      │ Fetch from    │  │ Fetch from   │
                      │ Langfuse      │  │ local file   │
                      └───┬───────┬───┘  └──────────────┘
                          │ OK    │ Fail
                          ▼       ▼
                      ┌───────┐ ┌──────────────┐
                      │ Cache │ │ Fetch from   │
                      │ Return│ │ local file   │
                      └───────┘ └──────────────┘
```

### Benefits

1. **Hot Reloading**: Update prompts in Langfuse, changes reflect after cache TTL
2. **A/B Testing**: Use labels to test different prompt versions
3. **Environment Management**: Different prompts for dev/staging/production
4. **Reliability**: Local fallback ensures system works offline
5. **Performance**: Caching reduces API calls and latency

---

## Feature 3: Prompt Synchronization

### Overview

The prompt synchronization system enables bidirectional sync between local files and Langfuse with conflict detection and resolution.

### Architecture

**Primary File**: [utils/prompt_sync.py](../utils/prompt_sync.py)

**CLI Tool**: [scripts/sync_prompts.py](../scripts/sync_prompts.py)

**Migration Tool**: [scripts/migrate_prompts_to_langfuse.py](../scripts/migrate_prompts_to_langfuse.py)

### How It Works

1. **Metadata Tracking** - `.prompt_metadata.json` stores sync state for each prompt
2. **Checksum-Based Detection** - SHA256 hashes detect local and remote changes
3. **Conflict Detection** - Compares current checksums with last-synced checksum
4. **Pull/Push Operations** - Download from or upload to Langfuse
5. **Conflict Resolution** - Choose to keep local or remote version

### Metadata Structure

**File**: [prompts/.prompt_metadata.json](../prompts/.prompt_metadata.json)

```json
{
  "prompts": {
    "reasoning-agent": {
      "local_file": "reasoning_agent.txt",
      "langfuse_name": "reasoning-agent",
      "local_checksum": "8bc1256943e33b5e961350b7f923e2628341f3be8269646b13a7dda72990e1ba",
      "langfuse_version": 2,
      "langfuse_label": "production",
      "last_synced": "2025-10-03T22:00:38.179721",
      "last_pulled": "2025-10-03T22:00:38.179734",
      "last_pushed": null,
      "sync_status": "synced",
      "last_synced_checksum": "8bc1256943e33b5e961350b7f923e2628341f3be8269646b13a7dda72990e1ba"
    }
  },
  "last_updated": "2025-10-03T22:00:59.080712"
}
```

### Sync Status States

| Status | Icon | Description |
|--------|------|-------------|
| `synced` | ✅ | Local and remote are identical |
| `modified_local` | 📝 | Local file has been changed |
| `modified_remote` | ☁️ | Remote version in Langfuse updated |
| `conflict` | ⚠️ | Both local and remote changed |
| `new_local` | 🆕 | Exists locally, not in Langfuse |
| `new_remote` | 🌐 | Exists in Langfuse, not locally |
| `not_found` | ❌ | Not found in either location |

### CLI Commands

#### Initialize Metadata

**First-time setup**:
```bash
python scripts/sync_prompts.py init
```

**What it does**:
- Scans all local prompt files
- Calculates checksums
- Attempts to fetch versions from Langfuse
- Creates `.prompt_metadata.json`

#### Check Sync Status

```bash
# Check all prompts
python scripts/sync_prompts.py status

# Check specific prompts
python scripts/sync_prompts.py status --names reasoning-agent,validation-agent
```

**Output Example**:
```
✅ Synced (7)
   • reasoning-agent                              (reasoning_agent.txt)
   • info-retriever-agent                         (info_retriever_agent.txt)
   ...

📝 Modified locally (1)
   • execution-agent                              (execution_agent.txt)

☁️  Modified remotely (1)
   • validation-agent                             (validation_agent.txt)

⚠️  CONFLICT - both changed (1)
   • report-agent                                 (report_agent.txt)
```

#### Pull Prompts

```bash
# Pull all prompts
python scripts/sync_prompts.py pull

# Pull specific prompts
python scripts/sync_prompts.py pull --names reasoning-agent,validation-agent

# Pull with specific label
python scripts/sync_prompts.py pull --label staging

# Force overwrite local changes
python scripts/sync_prompts.py pull --force
```

**Safety**: Won't overwrite local changes unless `--force` is used.

#### Push Prompts

```bash
# Push all prompts
python scripts/sync_prompts.py push

# Push specific prompts
python scripts/sync_prompts.py push --names reasoning-agent

# Push with custom labels
python scripts/sync_prompts.py push --labels production,v2.0

# Force overwrite remote changes
python scripts/sync_prompts.py push --force
```

**Safety**: Won't overwrite remote changes unless `--force` is used.

#### Resolve Conflicts

```bash
# Keep local version (push to Langfuse)
python scripts/sync_prompts.py resolve reasoning-agent --strategy local

# Keep remote version (pull from Langfuse)
python scripts/sync_prompts.py resolve reasoning-agent --strategy remote
```

### Change Detection Algorithm

**File**: [utils/prompt_sync.py:265-333](../utils/prompt_sync.py#L265-L333)

```python
def check_sync_status(names):
    for langfuse_name in names:
        # Read local file
        local_content = self._read_local_prompt(local_file)
        local_checksum = self._calculate_checksum(local_content)

        # Fetch remote content
        remote_info = self._get_remote_prompt(langfuse_name)
        remote_checksum = self._calculate_checksum(remote_info[0])

        # Get last synced checksum from metadata
        last_synced_checksum = metadata.last_synced_checksum

        # Determine status
        local_changed = local_checksum != last_synced_checksum
        remote_changed = remote_checksum != last_synced_checksum

        if not local_changed and not remote_changed:
            status = "synced"
        elif local_changed and not remote_changed:
            status = "modified_local"
        elif not local_changed and remote_changed:
            status = "modified_remote"
        else:  # both changed
            status = "conflict"
```

### Migration Script

**File**: [scripts/migrate_prompts_to_langfuse.py](../scripts/migrate_prompts_to_langfuse.py)

**Purpose**: One-time upload of all local prompts to Langfuse

```bash
# Dry run (preview what will be uploaded)
python scripts/migrate_prompts_to_langfuse.py --dry-run

# Actually migrate
python scripts/migrate_prompts_to_langfuse.py

# Migrate and update metadata
python scripts/migrate_prompts_to_langfuse.py --update-metadata
```

**What it does**:
1. Reads all prompt files from `prompts/` directory
2. Uploads each to Langfuse with appropriate labels and config
3. Optionally initializes metadata file for sync tracking

### Workflow Examples

#### Scenario 1: Team Member Edits in Langfuse UI

1. Team member updates `reasoning-agent` in Langfuse UI
2. You check status: `python scripts/sync_prompts.py status`
3. Status shows: ☁️ Modified remotely
4. You pull: `python scripts/sync_prompts.py pull --names reasoning-agent`
5. Local file updated ✅

#### Scenario 2: You Edit Local Prompt

1. You edit `prompts/validation_agent.txt`
2. Status: `python scripts/sync_prompts.py status` → 📝 Modified locally
3. Push: `python scripts/sync_prompts.py push --names validation-agent`
4. Langfuse updated with new version ✅

#### Scenario 3: Conflict

1. You edit local, team member edits remote
2. Status shows: ⚠️ CONFLICT
3. Decide strategy (keep local or remote)
4. Resolve: `python scripts/sync_prompts.py resolve reasoning-agent --strategy local`
5. Conflict resolved ✅

---

## Code Locations Reference

### Configuration

| File | Lines | Purpose |
|------|-------|---------|
| [config/settings.py](../config/settings.py) | 13-27 | All Langfuse environment variables |

### Core Infrastructure

| File | Lines | Purpose |
|------|-------|---------|
| [utils/langfuse_config.py](../utils/langfuse_config.py) | 1-110 | Callback handlers and client initialization |
| [utils/langfuse_config.py](../utils/langfuse_config.py) | 112-247 | Prompt management helper functions |
| [utils/prompt_manager.py](../utils/prompt_manager.py) | 1-220 | PromptManager singleton class |
| [utils/prompt_sync.py](../utils/prompt_sync.py) | 1-594 | PromptSyncManager for bidirectional sync |

### Tracing Integration Points

| File | Lines | Purpose |
|------|-------|---------|
| [main.py](../main.py) | 42-71 | Main workflow tracing setup |
| [graph/nodes.py](../graph/nodes.py) | 294, 320-334 | Reasoning agent tracing |
| [graph/nodes.py](../graph/nodes.py) | 410, 474-488 | Report agent tracing |

### Prompt Management Integration

| File | Lines | Purpose |
|------|-------|---------|
| [agents/specialized_agents.py](../agents/specialized_agents.py) | 14-36 | Info retriever agent |
| [agents/specialized_agents.py](../agents/specialized_agents.py) | 42-62 | Execution agent |
| [agents/specialized_agents.py](../agents/specialized_agents.py) | 68-89 | Validation agent |
| [agents/specialized_agents.py](../agents/specialized_agents.py) | 95-116 | Reasoning agent |
| [agents/specialized_agents.py](../agents/specialized_agents.py) | 122-143 | Report agent |
| [graph/nodes.py](../graph/nodes.py) | 101-119 | Query refinement check node |
| [graph/nodes.py](../graph/nodes.py) | 199-217 | Ticket refinement node |

### CLI Tools

| File | Lines | Purpose |
|------|-------|---------|
| [scripts/sync_prompts.py](../scripts/sync_prompts.py) | 1-447 | Complete CLI for sync operations |
| [scripts/migrate_prompts_to_langfuse.py](../scripts/migrate_prompts_to_langfuse.py) | 1-252 | One-time migration script |

### Data Files

| File | Purpose |
|------|---------|
| [prompts/.prompt_metadata.json](../prompts/.prompt_metadata.json) | Sync metadata tracking |
| `prompts/*.txt` | Local prompt files |

---

## Setup Guide

### Prerequisites

1. **Python 3.8+** (currently using 3.11.12)
2. **Langfuse Instance**:
   - Option A: [Langfuse Cloud](https://cloud.langfuse.com) (free tier available)
   - Option B: [Self-hosted Langfuse](https://langfuse.com/docs/deployment/self-host)

### Step 1: Install Dependencies

```bash
# Activate virtual environment
source .venv/bin/activate

# Install/update Langfuse SDK
pip install -r requirements.txt
# or
pip install langfuse>=2.0.0
```

### Step 2: Get Langfuse Credentials

#### For Langfuse Cloud:

1. Sign up at [cloud.langfuse.com](https://cloud.langfuse.com)
2. Create a new project
3. Go to **Settings** → **API Keys**
4. Copy `Public Key` and `Secret Key`

#### For Self-Hosted:

1. Deploy Langfuse using [Docker Compose](https://langfuse.com/docs/deployment/self-host)
2. Access your instance (e.g., `http://localhost:3000`)
3. Create a project and get API keys

### Step 3: Configure Environment Variables

Edit your `.env` file:

```bash
# OpenAI Configuration (existing)
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.1
OPENAI_MAX_TOKENS=4000

# Langfuse Core Configuration
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key-here
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key-here
LANGFUSE_HOST=https://cloud.langfuse.com
# OR for self-hosted:
# LANGFUSE_HOST=http://localhost:3000

# Langfuse Prompt Management
LANGFUSE_PROMPT_MANAGEMENT_ENABLED=true
LANGFUSE_PROMPT_FALLBACK_TO_LOCAL=true
LANGFUSE_PROMPT_CACHE_TTL=300

# Langfuse Prompt Sync
LANGFUSE_PROMPT_SYNC_METADATA_FILE=prompts/.prompt_metadata.json
LANGFUSE_PROMPT_SYNC_AUTO_RESOLVE=false
LANGFUSE_PROMPT_SYNC_DEFAULT_LABEL=production
```

### Step 4: Migrate Prompts to Langfuse

**First-time setup**: Upload existing prompts to Langfuse

```bash
# Preview what will be uploaded
python scripts/migrate_prompts_to_langfuse.py --dry-run

# Actually migrate
python scripts/migrate_prompts_to_langfuse.py --update-metadata
```

**Expected output**:
```
✅ Uploading: reasoning_agent.txt → reasoning-agent... SUCCESS
✅ Uploading: info_retriever_agent.txt → info-retriever-agent... SUCCESS
...

🎉 Migration completed!
✅ Metadata updated successfully
```

### Step 5: Verify Setup

#### Check Prompt Sync Status

```bash
python scripts/sync_prompts.py status
```

**Expected**: All prompts should show ✅ Synced

#### Run a Test Workflow

```bash
python main.py
```

**Expected**:
- Workflow executes successfully
- Console shows "LangFuse tracing enabled for this execution"
- Check Langfuse dashboard for traces

#### View Traces in Langfuse

1. Open Langfuse dashboard
2. Navigate to **Traces** section
3. You should see traces for the test session
4. Click on a trace to inspect details

### Step 6: Test Prompt Hot-Reload (Optional)

1. Edit a prompt in Langfuse UI
2. Wait for cache TTL (5 minutes) or restart application
3. Run workflow again
4. Verify the new prompt is used

---

## Usage Examples

### Example 1: Debugging a Failed Ticket Resolution

**Scenario**: A ticket failed to resolve, and you need to understand why.

**Steps**:

1. **Find the session ID** from the error log or `sessions/` directory
   ```
   sessions/10042025_1814_c280/
   ```

2. **Open Langfuse dashboard** and filter by session ID: `10042025_1814_c280`

3. **Inspect the trace**:
   - View the reasoning agent's prompt and response
   - Check if the execution agent encountered errors
   - See token usage for each step

4. **Identify the issue**:
   - Maybe the reasoning agent misunderstood the ticket
   - Or the execution agent failed a database operation

5. **Fix and verify**:
   - Update the prompt in Langfuse or locally
   - Re-run the workflow
   - Compare traces to see improvements

### Example 2: A/B Testing Prompt Versions

**Scenario**: You want to test if a new reasoning agent prompt performs better.

**Steps**:

1. **Create a new prompt version in Langfuse**:
   - Go to Langfuse UI → Prompts → `reasoning-agent`
   - Click "Create Version"
   - Edit the prompt text
   - Add label: `experiment-v2`

2. **Update configuration** to use the new version:
   ```python
   # In agents/specialized_agents.py
   prompt_data = prompt_manager.get_prompt("reasoning-agent", label="experiment-v2")
   ```

3. **Run test cases** with both versions

4. **Compare in Langfuse**:
   - Filter traces by prompt version
   - Compare success rates, token usage, response quality

5. **Promote to production** if experiment succeeds:
   - Add `production` label to the new version in Langfuse
   - Revert code to use `label="production"`

### Example 3: Team Collaboration on Prompts

**Scenario**: Multiple team members need to update prompts.

**Workflow**:

1. **Developer A**: Edits `validation-agent` prompt in Langfuse UI
   - Makes changes in the web interface
   - Adds label: `production`

2. **Developer B**: Wants to use the updated prompt locally
   ```bash
   # Check what changed
   python scripts/sync_prompts.py status
   # Output: ☁️  validation-agent - Modified remotely

   # Pull the changes
   python scripts/sync_prompts.py pull --names validation-agent
   # Output: ✅ Pulled 'validation-agent' (version 3)
   ```

3. **Developer B**: Tests locally with new prompt
   ```bash
   python main.py
   ```

4. **Developer B**: Makes further improvements locally
   - Edits `prompts/validation_agent.txt`
   - Tests the changes

5. **Developer B**: Pushes improvements back to Langfuse
   ```bash
   python scripts/sync_prompts.py push --names validation-agent
   # Output: ✅ Pushed 'validation-agent' (version 4)
   ```

6. **Developer A**: Pulls the latest version
   ```bash
   python scripts/sync_prompts.py pull
   ```

### Example 4: Monitoring Production Costs

**Scenario**: You want to track token costs in production.

**Steps**:

1. **Run production workflows** with Langfuse enabled

2. **Open Langfuse dashboard** → Analytics

3. **View metrics**:
   - Total token usage (prompt + completion)
   - Cost estimates per model
   - Cost breakdown by agent type
   - Cost per session/ticket

4. **Optimize** if costs are high:
   - Identify expensive agents (check avg tokens per call)
   - Review prompts to reduce verbosity
   - Consider using smaller models for certain agents
   - Adjust `max_tokens` in prompt metadata

5. **Track improvements**:
   - Compare metrics before/after optimization
   - Monitor ongoing costs

### Example 5: Rolling Back a Bad Prompt

**Scenario**: You updated a prompt, but it's performing poorly in production.

**Steps**:

1. **Identify the issue** in Langfuse traces
   - See increased error rates or poor responses

2. **Check prompt version history** in Langfuse UI
   - Find the last known good version

3. **Roll back**:
   ```bash
   # Pull specific version (if you know the version number)
   # Note: Current implementation uses labels, not version numbers
   # Workaround: Manually copy the old version from Langfuse UI to local file

   # Or: Change the label in Langfuse UI
   # Set the "production" label to point to the older version

   # Then pull
   python scripts/sync_prompts.py pull --names reasoning-agent
   ```

4. **Restart application** (to clear cache)

5. **Verify** rollback worked by checking new traces

### Example 6: Environment-Specific Prompts

**Scenario**: Use different prompts for development and production.

**Setup**:

1. **Create environment-specific prompts** in Langfuse:
   - `reasoning-agent` with label `production`
   - `reasoning-agent` with label `development`

2. **Configure environment variable**:
   ```bash
   # In .env.development
   LANGFUSE_PROMPT_SYNC_DEFAULT_LABEL=development

   # In .env.production
   LANGFUSE_PROMPT_SYNC_DEFAULT_LABEL=production
   ```

3. **Update code** to use environment-specific label:
   ```python
   from config.settings import LANGFUSE_PROMPT_SYNC_DEFAULT_LABEL

   prompt_data = prompt_manager.get_prompt(
       "reasoning-agent",
       label=LANGFUSE_PROMPT_SYNC_DEFAULT_LABEL
   )
   ```

4. **Switch environments** by changing `.env` file or env vars

---

## Troubleshooting

### Common Issues

#### 1. "LangFuse client not available"

**Symptoms**:
```
Warning: Failed to initialize LangFuse client: ...
Warning: LangFuse credentials not configured. Skipping tracing.
```

**Causes**:
- `LANGFUSE_ENABLED=false` or not set
- Missing `LANGFUSE_PUBLIC_KEY` or `LANGFUSE_SECRET_KEY`
- Incorrect Langfuse host URL
- Network connectivity issues

**Solutions**:
```bash
# Check .env file
cat .env | grep LANGFUSE

# Verify variables are set
echo $LANGFUSE_ENABLED
echo $LANGFUSE_PUBLIC_KEY

# Test connection
python -c "
from utils.langfuse_config import get_langfuse_client
client = get_langfuse_client()
print('Connected!' if client else 'Failed')
"

# Common fixes:
# 1. Set LANGFUSE_ENABLED=true
# 2. Add correct API keys
# 3. Use correct host URL (cloud.langfuse.com or localhost:3000)
```

#### 2. "Prompts still using local files"

**Symptoms**:
- Changes in Langfuse don't reflect in application
- Always falls back to local files

**Causes**:
- `LANGFUSE_PROMPT_MANAGEMENT_ENABLED=false`
- Cache TTL hasn't expired yet
- Prompt fetch failing silently

**Solutions**:
```bash
# Check configuration
echo $LANGFUSE_PROMPT_MANAGEMENT_ENABLED  # Should be "true"
echo $LANGFUSE_PROMPT_FALLBACK_TO_LOCAL   # Can be true or false

# Clear cache and restart
python -c "
from utils.prompt_manager import get_prompt_manager
pm = get_prompt_manager()
pm.clear_cache()
print('Cache cleared')
"

# Test prompt fetching
python -c "
from utils.prompt_manager import get_prompt_manager
pm = get_prompt_manager()
prompt_data = pm.get_prompt('reasoning-agent', label='production')
print(f'Fetched: {prompt_data.name}, Version: {prompt_data.version}')
"
```

#### 3. "Conflict detected" during sync

**Symptoms**:
```
⚠️  CONFLICT - both changed (1)
   • reasoning-agent
```

**Causes**:
- Local file edited
- Remote file edited in Langfuse
- Both changed since last sync

**Solutions**:
```bash
# Option 1: Keep local version
python scripts/sync_prompts.py resolve reasoning-agent --strategy local

# Option 2: Keep remote version
python scripts/sync_prompts.py resolve reasoning-agent --strategy remote

# Option 3: Manual merge
# 1. View local version: cat prompts/reasoning_agent.txt
# 2. View remote version in Langfuse UI
# 3. Manually merge changes
# 4. Push merged version: python scripts/sync_prompts.py push --names reasoning-agent --force
```

#### 4. "No traces appearing in Langfuse"

**Symptoms**:
- Workflow runs successfully
- No traces in Langfuse dashboard

**Causes**:
- Callbacks not attached to config
- Langfuse handler failed to initialize
- Wrong project selected in dashboard

**Solutions**:
```bash
# Verify handler is created
grep "LangFuse tracing enabled" <(python main.py 2>&1)

# Check if callbacks are attached
python -c "
from utils.langfuse_config import get_langfuse_handler
handler = get_langfuse_handler(session_id='test')
print(f'Handler created: {handler is not None}')
"

# Test with minimal example
python -c "
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from utils.langfuse_config import get_langfuse_handler

handler = get_langfuse_handler(session_id='test_trace')
llm = ChatOpenAI()

response = llm.invoke(
    [HumanMessage(content='Hello')],
    config={'callbacks': [handler]}
)
print(f'Response: {response.content}')
print('Check Langfuse dashboard for trace with session_id: test_trace')
"
```

#### 5. "Metadata file out of sync"

**Symptoms**:
- Status shows incorrect sync states
- Conflicts detected when none exist

**Causes**:
- Metadata file corrupted or outdated
- Manual file edits without updating metadata

**Solutions**:
```bash
# Reinitialize metadata
python scripts/sync_prompts.py init --force

# Or manually delete and recreate
rm prompts/.prompt_metadata.json
python scripts/sync_prompts.py init
```

#### 6. "Module 'langfuse' not found"

**Symptoms**:
```
ModuleNotFoundError: No module named 'langfuse'
```

**Solutions**:
```bash
# Install Langfuse SDK
pip install langfuse>=2.0.0

# Or install all requirements
pip install -r requirements.txt

# Verify installation
python -c "import langfuse; print(langfuse.__version__)"
```

#### 7. "High API call volume to Langfuse"

**Symptoms**:
- Slow performance
- Rate limiting errors

**Causes**:
- Cache TTL too low
- Fetching prompts on every request

**Solutions**:
```bash
# Increase cache TTL in .env
LANGFUSE_PROMPT_CACHE_TTL=600  # 10 minutes instead of 5

# Verify caching is working
python -c "
from utils.prompt_manager import get_prompt_manager
pm = get_prompt_manager()
print(pm.get_cache_stats())
"
```

### Debug Mode

Enable verbose logging to troubleshoot:

```python
# Add to top of main.py for debugging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Check Script

Create a health check script to verify all Langfuse features:

```python
#!/usr/bin/env python3
"""Langfuse Integration Health Check"""

from utils.langfuse_config import get_langfuse_client, get_langfuse_handler
from utils.prompt_manager import get_prompt_manager
from config.settings import *

print("=" * 60)
print("Langfuse Integration Health Check")
print("=" * 60)

# 1. Configuration
print("\n1. Configuration")
print(f"   LANGFUSE_ENABLED: {LANGFUSE_ENABLED}")
print(f"   LANGFUSE_HOST: {LANGFUSE_HOST}")
print(f"   LANGFUSE_PUBLIC_KEY: {'✅ Set' if LANGFUSE_PUBLIC_KEY else '❌ Missing'}")
print(f"   LANGFUSE_SECRET_KEY: {'✅ Set' if LANGFUSE_SECRET_KEY else '❌ Missing'}")

# 2. Client Connection
print("\n2. Client Connection")
client = get_langfuse_client()
print(f"   Langfuse Client: {'✅ Connected' if client else '❌ Failed'}")

# 3. Callback Handler
print("\n3. Callback Handler")
handler = get_langfuse_handler(session_id="health_check")
print(f"   Callback Handler: {'✅ Created' if handler else '❌ Failed'}")

# 4. Prompt Management
print("\n4. Prompt Management")
print(f"   LANGFUSE_PROMPT_MANAGEMENT_ENABLED: {LANGFUSE_PROMPT_MANAGEMENT_ENABLED}")
pm = get_prompt_manager()
try:
    prompt_data = pm.get_prompt("reasoning-agent", label="production")
    print(f"   Prompt Fetch: ✅ Success (version: {prompt_data.version})")
except Exception as e:
    print(f"   Prompt Fetch: ❌ Failed ({e})")

# 5. Cache Stats
print("\n5. Cache Statistics")
stats = pm.get_cache_stats()
print(f"   Cached Prompts: {stats['cached_prompts']}")
print(f"   Langfuse Enabled: {stats['langfuse_enabled']}")

print("\n" + "=" * 60)
print("Health Check Complete")
print("=" * 60)
```

Run with:
```bash
python scripts/health_check.py
```

---

## Best Practices

### 1. Prompt Management

#### ✅ DO:
- Use descriptive labels (`production`, `staging`, `experiment-v2`)
- Version prompts before major changes
- Test prompt changes in non-production environments first
- Include model configuration in Langfuse prompt metadata
- Document prompt changes in Langfuse UI (use description field)

#### ❌ DON'T:
- Deploy untested prompts directly to production
- Use generic labels like `v1`, `v2` without context
- Mix production and experimental prompts without clear labeling
- Forget to update metadata after manual Langfuse UI edits

### 2. Synchronization

#### ✅ DO:
- Run `status` before `push` or `pull`
- Use `--force` only when you're certain
- Commit `.prompt_metadata.json` to version control (in team environments)
- Resolve conflicts promptly
- Pull before editing locally
- Push after local edits

#### ❌ DON'T:
- Ignore conflict warnings
- Edit both locally and remotely simultaneously without syncing
- Delete `.prompt_metadata.json` (unless reinitializing)
- Use `--force` as default behavior

### 3. Tracing

#### ✅ DO:
- Use meaningful session IDs that correlate with your application's sessions
- Add custom metadata to traces for easier filtering
- Regularly review traces for errors and performance issues
- Use session correlation to debug multi-agent workflows
- Monitor token costs via Langfuse analytics

#### ❌ DON'T:
- Include sensitive data in prompts or metadata
- Ignore failed traces in production
- Disable tracing in production (unless necessary for performance)

### 4. Configuration

#### ✅ DO:
- Use environment-specific `.env` files
- Keep API keys in `.env` (never commit to git)
- Enable fallback to local files for reliability
- Set appropriate cache TTL based on your update frequency
- Document configuration changes

#### ❌ DON'T:
- Hardcode API keys in source files
- Commit `.env` to version control
- Disable fallback in production environments
- Set cache TTL too low (increases API calls)

### 5. Team Collaboration

#### ✅ DO:
- Communicate before making major prompt changes
- Use labels to manage different environments
- Document the reason for prompt changes
- Review prompt changes via Langfuse UI before pulling
- Establish a prompt change approval process for production

#### ❌ DON'T:
- Make production changes without team awareness
- Overwrite others' changes without review
- Skip conflict resolution

### 6. Performance

#### ✅ DO:
- Use caching to reduce Langfuse API calls
- Monitor trace volume and costs
- Batch prompt updates when possible
- Optimize prompts to reduce token usage

#### ❌ DON'T:
- Fetch prompts on every request (use cache)
- Set cache TTL to 0 (defeats caching)
- Create excessive traces for debugging (use sampling if needed)

### 7. Security

#### ✅ DO:
- Rotate API keys periodically
- Use separate Langfuse projects for dev/staging/prod
- Restrict access to production Langfuse project
- Review traces for accidentally logged sensitive data

#### ❌ DON'T:
- Share API keys across environments
- Log PII or credentials in prompts
- Make Langfuse project publicly accessible

---

## Additional Resources

### Official Langfuse Documentation
- [Langfuse Docs](https://langfuse.com/docs)
- [Python SDK Reference](https://langfuse.com/docs/sdk/python)
- [LangChain Integration](https://langfuse.com/docs/integrations/langchain)
- [Prompt Management](https://langfuse.com/docs/prompts)
- [Self-Hosting Guide](https://langfuse.com/docs/deployment/self-host)

### Related Project Documentation
- [PROMPT_SYNC.md](./PROMPT_SYNC.md) - Detailed prompt synchronization documentation
- [CLAUDE.md](../CLAUDE.md) - Project overview and architecture
- [README.md](../README.md) - Getting started guide

### Example Workflows
- See [Usage Examples](#usage-examples) section above

### Support
- Langfuse Discord: [discord.gg/langfuse](https://discord.gg/langfuse)
- GitHub Issues: [github.com/langfuse/langfuse/issues](https://github.com/langfuse/langfuse/issues)

---

## Summary

This project fully integrates Langfuse across three major capabilities:

1. **Observability & Tracing** 🔍
   - Track all LLM calls and agent decisions
   - Session-correlated debugging
   - Cost and performance monitoring

2. **Centralized Prompt Management** 📝
   - Version control for prompts
   - Hot-reload without code changes
   - A/B testing and experimentation

3. **Bidirectional Synchronization** 🔄
   - Team collaboration on prompts
   - Conflict detection and resolution
   - Local-remote consistency

All features are **production-ready**, **configurable**, and **fallback-safe**, ensuring the system works reliably even when Langfuse is temporarily unavailable.

For questions or issues, refer to the [Troubleshooting](#troubleshooting) section or consult the [Code Locations Reference](#code-locations-reference) for specific implementation details.

---

**Last Updated**: October 4, 2025
**Langfuse SDK Version**: >=2.0.0
**Project**: RCS Standalone Code - Agentic RAG Ticket Resolution System
