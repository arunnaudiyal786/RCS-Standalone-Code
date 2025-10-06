# Prompt Synchronization System

This document describes the bidirectional prompt synchronization system between local prompt files and Langfuse.

## Overview

The prompt sync system enables:
- **Pull**: Download prompts from Langfuse to local `prompts/` directory
- **Push**: Upload local prompt files to Langfuse
- **Sync Management**: Track changes, detect conflicts, manage versions with metadata

## Architecture

### Components

1. **PromptSyncManager** (`utils/prompt_sync.py`)
   - Core synchronization logic
   - Checksum-based change detection
   - Conflict resolution
   - Metadata management

2. **Metadata File** (`prompts/.prompt_metadata.json`)
   - Tracks sync state for each prompt
   - Stores checksums, versions, timestamps
   - Enables conflict detection

3. **CLI Interface** (`scripts/sync_prompts.py`)
   - User-friendly command-line tool
   - Supports pull, push, status, resolve, init commands

4. **Configuration** (`config/settings.py`)
   - Environment-based configuration
   - Customizable metadata location
   - Auto-resolve settings

## Usage

### Initialize Metadata

Before using the sync system, initialize the metadata file:

```bash
python3 scripts/sync_prompts.py init
```

This scans all local prompts and creates the metadata tracking file.

### Check Sync Status

View the current sync status of all prompts:

```bash
# Check all prompts
python3 scripts/sync_prompts.py status

# Check specific prompts
python3 scripts/sync_prompts.py status --names reasoning-agent,validation-agent
```

Status indicators:
- ✅ **Synced**: Local and remote are identical
- 📝 **Modified locally**: Local file has been changed
- ☁️ **Modified remotely**: Remote version in Langfuse has been updated
- ⚠️ **CONFLICT**: Both local and remote have been modified
- 🆕 **New (local only)**: Prompt exists locally but not in Langfuse
- 🌐 **New (remote only)**: Prompt exists in Langfuse but not locally

### Pull Prompts from Langfuse

Download prompts from Langfuse to local files:

```bash
# Pull all prompts
python3 scripts/sync_prompts.py pull

# Pull specific prompts
python3 scripts/sync_prompts.py pull --names reasoning-agent,validation-agent

# Pull with specific label
python3 scripts/sync_prompts.py pull --label staging

# Force overwrite local changes
python3 scripts/sync_prompts.py pull --force
```

**Safety**: By default, pull will NOT overwrite local changes. Use `--force` to override.

### Push Prompts to Langfuse

Upload local prompts to Langfuse:

```bash
# Push all prompts
python3 scripts/sync_prompts.py push

# Push specific prompts
python3 scripts/sync_prompts.py push --names reasoning-agent

# Push with custom labels
python3 scripts/sync_prompts.py push --labels production,v2.0

# Force overwrite remote changes
python3 scripts/sync_prompts.py push --force
```

**Safety**: By default, push will NOT overwrite remote changes. Use `--force` to override.

### Resolve Conflicts

When both local and remote versions have been modified, resolve manually:

```bash
# Keep local version (push to Langfuse)
python3 scripts/sync_prompts.py resolve reasoning-agent --strategy local

# Keep remote version (pull from Langfuse)
python3 scripts/sync_prompts.py resolve reasoning-agent --strategy remote
```

## Metadata Structure

The `.prompt_metadata.json` file stores sync information:

```json
{
  "prompts": {
    "reasoning-agent": {
      "local_file": "reasoning_agent.txt",
      "langfuse_name": "reasoning-agent",
      "local_checksum": "abc123...",
      "langfuse_version": 2,
      "langfuse_label": "production",
      "last_synced": "2025-10-03T22:00:00Z",
      "last_pulled": "2025-10-03T21:30:00Z",
      "last_pushed": "2025-10-03T20:00:00Z",
      "sync_status": "synced",
      "last_synced_checksum": "abc123..."
    }
  },
  "last_updated": "2025-10-03T22:00:00Z"
}
```

### Metadata Fields

- `local_file`: Local filename (e.g., `reasoning_agent.txt`)
- `langfuse_name`: Langfuse prompt name (kebab-case, e.g., `reasoning-agent`)
- `local_checksum`: SHA256 hash of current local content
- `langfuse_version`: Version number in Langfuse
- `langfuse_label`: Label used for fetching (default: `production`)
- `last_synced`: ISO timestamp of last successful sync
- `last_pulled`: ISO timestamp of last pull operation
- `last_pushed`: ISO timestamp of last push operation
- `sync_status`: Current status (`synced`, `modified_local`, `modified_remote`, `conflict`)
- `last_synced_checksum`: SHA256 hash at time of last sync (used for conflict detection)

## Configuration

Environment variables in `.env`:

```bash
# Enable/disable sync features
LANGFUSE_ENABLED=true
LANGFUSE_PROMPT_MANAGEMENT_ENABLED=true

# Langfuse credentials
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3000

# Sync-specific settings
LANGFUSE_PROMPT_SYNC_METADATA_FILE=prompts/.prompt_metadata.json
LANGFUSE_PROMPT_SYNC_AUTO_RESOLVE=false
LANGFUSE_PROMPT_SYNC_DEFAULT_LABEL=production
```

## Workflow Examples

### Scenario 1: Team Member Edits Prompt in Langfuse UI

1. Team member updates `reasoning-agent` prompt in Langfuse UI
2. You check status: `python3 scripts/sync_prompts.py status`
3. Status shows: ☁️ Modified remotely
4. You pull changes: `python3 scripts/sync_prompts.py pull --names reasoning-agent`
5. Local file is updated with remote version

### Scenario 2: You Edit Local Prompt

1. You modify `prompts/validation_agent.txt` locally
2. You check status: `python3 scripts/sync_prompts.py status`
3. Status shows: 📝 Modified locally
4. You push changes: `python3 scripts/sync_prompts.py push --names validation-agent`
5. Langfuse is updated with new version

### Scenario 3: Conflict Resolution

1. You edit local prompt
2. Team member edits same prompt in Langfuse
3. Status shows: ⚠️ CONFLICT
4. You decide to keep your local version:
   ```bash
   python3 scripts/sync_prompts.py resolve reasoning-agent --strategy local
   ```
5. Your local version is pushed to Langfuse, overwriting remote changes

## Integration with Migration Script

The original migration script has been enhanced:

```bash
# Migrate and update metadata
python3 scripts/migrate_prompts_to_langfuse.py --update-metadata

# Dry run to preview
python3 scripts/migrate_prompts_to_langfuse.py --dry-run
```

## Best Practices

1. **Check Status Regularly**: Run `status` command before making changes
2. **Pull Before Push**: Always pull latest changes before pushing
3. **Use Specific Names**: When working on specific prompts, use `--names` to avoid unnecessary syncs
4. **Version Control**: Commit `.prompt_metadata.json` to git if working in a team
5. **Force with Caution**: Only use `--force` when you're certain you want to overwrite changes
6. **Label Management**: Use labels (e.g., `staging`, `production`) to manage different environments

## Troubleshooting

### Problem: "Langfuse client not available"

**Solution**: Check that:
- `LANGFUSE_ENABLED=true` in `.env`
- `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are set
- Langfuse server is running (if self-hosted)

### Problem: "Conflict detected"

**Solution**: Use the `resolve` command with appropriate strategy:
```bash
python3 scripts/sync_prompts.py resolve <prompt-name> --strategy <local|remote>
```

### Problem: Metadata out of sync

**Solution**: Reinitialize metadata:
```bash
python3 scripts/sync_prompts.py init --force
```

### Problem: "No module named 'langfuse'"

**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
# or
python3 -m pip install langfuse>=2.0.0
```

## Technical Details

### Change Detection

The system uses SHA256 checksums to detect changes:
- **Local changes**: Compare current file checksum with `local_checksum` in metadata
- **Remote changes**: Compare remote content checksum with `last_synced_checksum`
- **Conflicts**: Both checksums differ from `last_synced_checksum`

### Prompt Name Mapping

Local files use snake_case (e.g., `reasoning_agent.txt`), while Langfuse uses kebab-case (e.g., `reasoning-agent`). The mapping is defined in `utils/prompt_sync.py`:

```python
PROMPT_NAME_MAPPING = {
    "reasoning_agent.txt": "reasoning-agent",
    "info_retriever_agent.txt": "info-retriever-agent",
    # ... etc
}
```

### Version Management

Langfuse automatically increments version numbers on each update. The sync system tracks:
- Latest version number after pull/push
- Supports fetching specific versions (future enhancement)

## API Reference

### PromptSyncManager

```python
from utils.prompt_sync import PromptSyncManager

manager = PromptSyncManager()

# Check status
status_map = manager.check_sync_status(names=["reasoning-agent"])

# Pull prompts
results = manager.pull_prompts(names=["reasoning-agent"], label="production", force=False)

# Push prompts
results = manager.push_prompts(names=["reasoning-agent"], force=False, labels=["production"])

# Resolve conflict
success = manager.resolve_conflict("reasoning-agent", strategy="local")

# Initialize metadata
success = manager.initialize_metadata()
```

## Future Enhancements

Potential improvements:
- Automatic conflict resolution strategies
- Diff visualization for conflicting changes
- Batch operations with progress tracking
- Support for prompt templates and variables
- Integration with CI/CD pipelines
- Rollback to previous versions
- Prompt history and audit log
