"""
Langfuse Prompt Synchronization Manager

Provides bidirectional synchronization between local prompt files and Langfuse,
with conflict detection, version tracking, and metadata management.
"""
import os
import json
import hashlib
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime
from pathlib import Path
from langfuse import Langfuse

from config.settings import (
    LANGFUSE_PUBLIC_KEY,
    LANGFUSE_SECRET_KEY,
    LANGFUSE_HOST,
    LANGFUSE_ENABLED,
    LANGFUSE_PROMPT_SYNC_METADATA_FILE,
    LANGFUSE_PROMPT_SYNC_DEFAULT_LABEL
)


# Mapping of local file names to Langfuse prompt names (kebab-case)
PROMPT_NAME_MAPPING = {
    "reasoning_agent.txt": "reasoning-agent",
    "info_retriever_agent.txt": "info-retriever-agent",
    "execution_agent.txt": "execution-agent",
    "validation_agent.txt": "validation-agent",
    "supervisor_agent.txt": "supervisor-agent",
    "report_agent.txt": "report-agent",
    "query_refinement_check.txt": "query-refinement-check",
    "ticket_refinement.txt": "ticket-refinement",
    "query_refinement_check_with_refined.txt": "query-refinement-check-with-refined"
}

# Reverse mapping for convenience
LANGFUSE_NAME_TO_FILE = {v: k for k, v in PROMPT_NAME_MAPPING.items()}


class SyncStatus:
    """Enumeration of sync status states"""
    SYNCED = "synced"
    MODIFIED_LOCAL = "modified_local"
    MODIFIED_REMOTE = "modified_remote"
    CONFLICT = "conflict"
    NEW_LOCAL = "new_local"
    NEW_REMOTE = "new_remote"
    NOT_FOUND = "not_found"


class PromptMetadata:
    """Metadata for a single prompt"""
    def __init__(
        self,
        local_file: str,
        langfuse_name: str,
        local_checksum: Optional[str] = None,
        langfuse_version: Optional[int] = None,
        langfuse_label: str = "production",
        last_synced: Optional[str] = None,
        last_pulled: Optional[str] = None,
        last_pushed: Optional[str] = None,
        sync_status: str = SyncStatus.SYNCED,
        last_synced_checksum: Optional[str] = None
    ):
        self.local_file = local_file
        self.langfuse_name = langfuse_name
        self.local_checksum = local_checksum
        self.langfuse_version = langfuse_version
        self.langfuse_label = langfuse_label
        self.last_synced = last_synced
        self.last_pulled = last_pulled
        self.last_pushed = last_pushed
        self.sync_status = sync_status
        self.last_synced_checksum = last_synced_checksum

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "local_file": self.local_file,
            "langfuse_name": self.langfuse_name,
            "local_checksum": self.local_checksum,
            "langfuse_version": self.langfuse_version,
            "langfuse_label": self.langfuse_label,
            "last_synced": self.last_synced,
            "last_pulled": self.last_pulled,
            "last_pushed": self.last_pushed,
            "sync_status": self.sync_status,
            "last_synced_checksum": self.last_synced_checksum
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptMetadata":
        """Create from dictionary"""
        return cls(**data)


class PromptSyncManager:
    """
    Manages bidirectional synchronization between local prompts and Langfuse

    Features:
    - Pull prompts from Langfuse to local files
    - Push prompts from local files to Langfuse
    - Track changes with checksums and timestamps
    - Detect and resolve conflicts
    - Version management
    """

    def __init__(
        self,
        prompts_dir: str = "prompts",
        metadata_file: Optional[str] = None
    ):
        self.prompts_dir = Path(prompts_dir)
        self.metadata_file = Path(metadata_file or LANGFUSE_PROMPT_SYNC_METADATA_FILE)
        self._langfuse_client: Optional[Langfuse] = None
        self._metadata: Dict[str, PromptMetadata] = {}

        # Initialize Langfuse client
        if LANGFUSE_ENABLED and LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY:
            try:
                self._langfuse_client = Langfuse(
                    public_key=LANGFUSE_PUBLIC_KEY,
                    secret_key=LANGFUSE_SECRET_KEY,
                    host=LANGFUSE_HOST
                )
            except Exception as e:
                print(f"Warning: Failed to initialize Langfuse client: {e}")
                self._langfuse_client = None

        # Load existing metadata
        self._load_metadata()

    def _load_metadata(self):
        """Load metadata from JSON file"""
        if not self.metadata_file.exists():
            self._metadata = {}
            return

        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._metadata = {
                    name: PromptMetadata.from_dict(meta_dict)
                    for name, meta_dict in data.get("prompts", {}).items()
                }
        except Exception as e:
            print(f"Warning: Failed to load metadata from {self.metadata_file}: {e}")
            self._metadata = {}

    def _save_metadata(self):
        """Save metadata to JSON file"""
        # Ensure directory exists
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "prompts": {
                name: meta.to_dict()
                for name, meta in self._metadata.items()
            },
            "last_updated": datetime.now().isoformat()
        }

        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error: Failed to save metadata to {self.metadata_file}: {e}")

    def _calculate_checksum(self, content: str) -> str:
        """Calculate SHA256 checksum of content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _read_local_prompt(self, filename: str) -> Optional[str]:
        """Read local prompt file content"""
        file_path = self.prompts_dir / filename
        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            return None

    def _write_local_prompt(self, filename: str, content: str):
        """Write content to local prompt file"""
        file_path = self.prompts_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            raise Exception(f"Failed to write {filename}: {e}")

    def _get_remote_prompt(
        self,
        name: str,
        label: str = "production",
        version: Optional[int] = None
    ) -> Optional[Tuple[str, int, Dict]]:
        """
        Fetch prompt from Langfuse

        Returns:
            Tuple of (prompt_text, version, config) or None if not found
        """
        if not self._langfuse_client:
            raise Exception("Langfuse client not available")

        try:
            if version is not None:
                langfuse_prompt = self._langfuse_client.get_prompt(name, version=version)
            else:
                langfuse_prompt = self._langfuse_client.get_prompt(name, label=label)

            # Extract prompt text
            if hasattr(langfuse_prompt, 'get_langchain_prompt'):
                prompt_text = langfuse_prompt.get_langchain_prompt()
            else:
                prompt_text = langfuse_prompt.prompt

            version_num = langfuse_prompt.version if hasattr(langfuse_prompt, 'version') else None
            config = langfuse_prompt.config if hasattr(langfuse_prompt, 'config') else {}

            return (prompt_text, version_num, config)

        except Exception as e:
            print(f"Error fetching prompt '{name}' from Langfuse: {e}")
            return None

    def _push_to_langfuse(
        self,
        name: str,
        content: str,
        config: Optional[Dict] = None,
        labels: Optional[List[str]] = None
    ) -> bool:
        """
        Push prompt to Langfuse

        Returns:
            True if successful, False otherwise
        """
        if not self._langfuse_client:
            raise Exception("Langfuse client not available")

        try:
            self._langfuse_client.create_prompt(
                name=name,
                prompt=content,
                config=config or {},
                labels=labels or ["production"]
            )
            return True
        except Exception as e:
            print(f"Error pushing prompt '{name}' to Langfuse: {e}")
            return False

    def check_sync_status(self, names: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Check sync status for all or specified prompts

        Args:
            names: Optional list of Langfuse prompt names to check

        Returns:
            Dictionary mapping prompt names to their sync status
        """
        if names is None:
            names = list(LANGFUSE_NAME_TO_FILE.keys())

        status_map = {}

        for langfuse_name in names:
            # Get local file info
            local_file = LANGFUSE_NAME_TO_FILE.get(langfuse_name)
            if not local_file:
                status_map[langfuse_name] = SyncStatus.NOT_FOUND
                continue

            local_content = self._read_local_prompt(local_file)
            local_exists = local_content is not None

            # Get metadata
            metadata = self._metadata.get(langfuse_name)

            # Get remote info
            remote_info = None
            if self._langfuse_client:
                remote_info = self._get_remote_prompt(
                    langfuse_name,
                    label=metadata.langfuse_label if metadata else LANGFUSE_PROMPT_SYNC_DEFAULT_LABEL
                )

            remote_exists = remote_info is not None

            # Determine status
            if not local_exists and not remote_exists:
                status = SyncStatus.NOT_FOUND
            elif not local_exists and remote_exists:
                status = SyncStatus.NEW_REMOTE
            elif local_exists and not remote_exists:
                status = SyncStatus.NEW_LOCAL
            elif metadata is None:
                # No metadata - need to sync
                status = SyncStatus.MODIFIED_LOCAL
            else:
                # Both exist - check for changes
                local_checksum = self._calculate_checksum(local_content)
                remote_content = remote_info[0]
                remote_checksum = self._calculate_checksum(remote_content)

                local_changed = local_checksum != metadata.last_synced_checksum
                remote_changed = remote_checksum != metadata.last_synced_checksum

                if not local_changed and not remote_changed:
                    status = SyncStatus.SYNCED
                elif local_changed and not remote_changed:
                    status = SyncStatus.MODIFIED_LOCAL
                elif not local_changed and remote_changed:
                    status = SyncStatus.MODIFIED_REMOTE
                else:
                    status = SyncStatus.CONFLICT

            status_map[langfuse_name] = status

        return status_map

    def pull_prompts(
        self,
        names: Optional[List[str]] = None,
        label: str = "production",
        force: bool = False
    ) -> Dict[str, bool]:
        """
        Pull prompts from Langfuse to local files

        Args:
            names: Optional list of Langfuse prompt names to pull
            label: Label to fetch from Langfuse
            force: If True, overwrite local changes without checking

        Returns:
            Dictionary mapping prompt names to success status
        """
        if not self._langfuse_client:
            raise Exception("Langfuse client not available")

        if names is None:
            names = list(LANGFUSE_NAME_TO_FILE.keys())

        results = {}

        for langfuse_name in names:
            try:
                # Get local file name
                local_file = LANGFUSE_NAME_TO_FILE.get(langfuse_name)
                if not local_file:
                    print(f"Warning: No local file mapping for '{langfuse_name}'")
                    results[langfuse_name] = False
                    continue

                # Check for conflicts if not forcing
                if not force:
                    status = self.check_sync_status([langfuse_name])
                    if status.get(langfuse_name) == SyncStatus.CONFLICT:
                        print(f"Conflict detected for '{langfuse_name}'. Use --force to overwrite or resolve manually.")
                        results[langfuse_name] = False
                        continue
                    elif status.get(langfuse_name) == SyncStatus.MODIFIED_LOCAL:
                        print(f"Local changes detected for '{langfuse_name}'. Use --force to overwrite.")
                        results[langfuse_name] = False
                        continue

                # Fetch from Langfuse
                remote_info = self._get_remote_prompt(langfuse_name, label=label)
                if not remote_info:
                    print(f"Failed to fetch '{langfuse_name}' from Langfuse")
                    results[langfuse_name] = False
                    continue

                prompt_text, version, config = remote_info

                # Write to local file
                self._write_local_prompt(local_file, prompt_text)

                # Update metadata
                checksum = self._calculate_checksum(prompt_text)
                metadata = PromptMetadata(
                    local_file=local_file,
                    langfuse_name=langfuse_name,
                    local_checksum=checksum,
                    langfuse_version=version,
                    langfuse_label=label,
                    last_synced=datetime.now().isoformat(),
                    last_pulled=datetime.now().isoformat(),
                    sync_status=SyncStatus.SYNCED,
                    last_synced_checksum=checksum
                )
                self._metadata[langfuse_name] = metadata

                print(f"✅ Pulled '{langfuse_name}' (version {version})")
                results[langfuse_name] = True

            except Exception as e:
                print(f"Error pulling '{langfuse_name}': {e}")
                results[langfuse_name] = False

        # Save metadata
        self._save_metadata()

        return results

    def push_prompts(
        self,
        names: Optional[List[str]] = None,
        force: bool = False,
        labels: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Push prompts from local files to Langfuse

        Args:
            names: Optional list of Langfuse prompt names to push
            force: If True, overwrite remote changes without checking
            labels: Labels to apply to pushed prompts

        Returns:
            Dictionary mapping prompt names to success status
        """
        if not self._langfuse_client:
            raise Exception("Langfuse client not available")

        if names is None:
            names = list(LANGFUSE_NAME_TO_FILE.keys())

        if labels is None:
            labels = ["production"]

        results = {}

        for langfuse_name in names:
            try:
                # Get local file
                local_file = LANGFUSE_NAME_TO_FILE.get(langfuse_name)
                if not local_file:
                    print(f"Warning: No local file mapping for '{langfuse_name}'")
                    results[langfuse_name] = False
                    continue

                # Read local content
                content = self._read_local_prompt(local_file)
                if content is None:
                    print(f"Local file '{local_file}' not found")
                    results[langfuse_name] = False
                    continue

                # Check for conflicts if not forcing
                if not force:
                    status = self.check_sync_status([langfuse_name])
                    if status.get(langfuse_name) == SyncStatus.CONFLICT:
                        print(f"Conflict detected for '{langfuse_name}'. Use --force to overwrite or resolve manually.")
                        results[langfuse_name] = False
                        continue
                    elif status.get(langfuse_name) == SyncStatus.MODIFIED_REMOTE:
                        print(f"Remote changes detected for '{langfuse_name}'. Use --force to overwrite.")
                        results[langfuse_name] = False
                        continue

                # Prepare config (could be enhanced to read from metadata)
                config = {}
                metadata = self._metadata.get(langfuse_name)
                if metadata and hasattr(metadata, 'config'):
                    config = metadata.config or {}

                # Push to Langfuse
                success = self._push_to_langfuse(langfuse_name, content, config, labels)
                if not success:
                    results[langfuse_name] = False
                    continue

                # Fetch the new version info
                remote_info = self._get_remote_prompt(langfuse_name, label=labels[0])
                version = remote_info[1] if remote_info else None

                # Update metadata
                checksum = self._calculate_checksum(content)
                new_metadata = PromptMetadata(
                    local_file=local_file,
                    langfuse_name=langfuse_name,
                    local_checksum=checksum,
                    langfuse_version=version,
                    langfuse_label=labels[0],
                    last_synced=datetime.now().isoformat(),
                    last_pushed=datetime.now().isoformat(),
                    sync_status=SyncStatus.SYNCED,
                    last_synced_checksum=checksum
                )
                self._metadata[langfuse_name] = new_metadata

                print(f"✅ Pushed '{langfuse_name}' (version {version})")
                results[langfuse_name] = True

            except Exception as e:
                print(f"Error pushing '{langfuse_name}': {e}")
                results[langfuse_name] = False

        # Save metadata
        self._save_metadata()

        return results

    def resolve_conflict(
        self,
        name: str,
        strategy: str = "local"
    ) -> bool:
        """
        Resolve conflict for a specific prompt

        Args:
            name: Langfuse prompt name
            strategy: Resolution strategy - "local" (keep local) or "remote" (keep remote)

        Returns:
            True if resolved successfully, False otherwise
        """
        if strategy == "local":
            # Push local version
            return self.push_prompts([name], force=True).get(name, False)
        elif strategy == "remote":
            # Pull remote version
            return self.pull_prompts([name], force=True).get(name, False)
        else:
            raise ValueError(f"Invalid strategy: {strategy}. Must be 'local' or 'remote'")

    def initialize_metadata(self) -> bool:
        """
        Initialize metadata file from current local prompts

        Returns:
            True if successful, False otherwise
        """
        print("Initializing prompt metadata from local files...")

        for local_file, langfuse_name in PROMPT_NAME_MAPPING.items():
            file_path = self.prompts_dir / local_file

            if not file_path.exists():
                print(f"⚠️  Skipping {local_file} - file not found")
                continue

            try:
                content = self._read_local_prompt(local_file)
                if content is None:
                    continue

                checksum = self._calculate_checksum(content)

                # Try to get remote version info
                version = None
                if self._langfuse_client:
                    remote_info = self._get_remote_prompt(langfuse_name)
                    if remote_info:
                        version = remote_info[1]

                metadata = PromptMetadata(
                    local_file=local_file,
                    langfuse_name=langfuse_name,
                    local_checksum=checksum,
                    langfuse_version=version,
                    langfuse_label=LANGFUSE_PROMPT_SYNC_DEFAULT_LABEL,
                    last_synced=datetime.now().isoformat(),
                    sync_status=SyncStatus.SYNCED,
                    last_synced_checksum=checksum
                )

                self._metadata[langfuse_name] = metadata
                print(f"✅ Initialized metadata for '{langfuse_name}'")

            except Exception as e:
                print(f"❌ Error initializing metadata for '{langfuse_name}': {e}")

        # Save metadata
        self._save_metadata()
        print(f"\n✅ Metadata saved to {self.metadata_file}")
        return True
