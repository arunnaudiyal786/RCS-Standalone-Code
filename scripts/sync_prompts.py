#!/usr/bin/env python3
"""
Langfuse Prompt Synchronization CLI

Bidirectional synchronization between local prompt files and Langfuse.

Usage:
    # Pull prompts from Langfuse to local
    python scripts/sync_prompts.py pull [--names <names>] [--label <label>] [--force]

    # Push prompts from local to Langfuse
    python scripts/sync_prompts.py push [--names <names>] [--force] [--labels <labels>]

    # Check sync status
    python scripts/sync_prompts.py status [--names <names>]

    # Resolve conflicts
    python scripts/sync_prompts.py resolve <prompt-name> --strategy <local|remote>

    # Initialize metadata
    python scripts/sync_prompts.py init

Examples:
    # Pull all prompts
    python scripts/sync_prompts.py pull

    # Pull specific prompts
    python scripts/sync_prompts.py pull --names reasoning-agent,validation-agent

    # Push with force (overwrite remote changes)
    python scripts/sync_prompts.py push --force

    # Check status of all prompts
    python scripts/sync_prompts.py status

    # Resolve conflict by keeping local version
    python scripts/sync_prompts.py resolve reasoning-agent --strategy local
"""
import os
import sys
import argparse
from pathlib import Path
from typing import List, Optional

# Add parent directory to path to import project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.prompt_sync import PromptSyncManager, SyncStatus, LANGFUSE_NAME_TO_FILE
from config.settings import LANGFUSE_ENABLED


# Status icons for console output
STATUS_ICONS = {
    SyncStatus.SYNCED: "✅",
    SyncStatus.MODIFIED_LOCAL: "📝",
    SyncStatus.MODIFIED_REMOTE: "☁️ ",
    SyncStatus.CONFLICT: "⚠️ ",
    SyncStatus.NEW_LOCAL: "🆕",
    SyncStatus.NEW_REMOTE: "🌐",
    SyncStatus.NOT_FOUND: "❌"
}

STATUS_DESCRIPTIONS = {
    SyncStatus.SYNCED: "Synced",
    SyncStatus.MODIFIED_LOCAL: "Modified locally",
    SyncStatus.MODIFIED_REMOTE: "Modified remotely",
    SyncStatus.CONFLICT: "CONFLICT - both changed",
    SyncStatus.NEW_LOCAL: "New (local only)",
    SyncStatus.NEW_REMOTE: "New (remote only)",
    SyncStatus.NOT_FOUND: "Not found"
}


def print_header(title: str):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{title}")
    print("-" * len(title))


def parse_names(names_arg: Optional[str]) -> Optional[List[str]]:
    """Parse comma-separated names argument"""
    if not names_arg:
        return None
    return [name.strip() for name in names_arg.split(",")]


def parse_labels(labels_arg: Optional[str]) -> List[str]:
    """Parse comma-separated labels argument"""
    if not labels_arg:
        return ["production"]
    return [label.strip() for label in labels_arg.split(",")]


def cmd_pull(args):
    """Pull prompts from Langfuse to local files"""
    print_header("Pull Prompts from Langfuse")

    if not LANGFUSE_ENABLED:
        print("❌ Error: Langfuse is not enabled. Set LANGFUSE_ENABLED=true in .env")
        return 1

    manager = PromptSyncManager()
    names = parse_names(args.names)

    if names:
        print(f"Pulling prompts: {', '.join(names)}")
    else:
        print("Pulling all prompts")

    print(f"Label: {args.label}")
    print(f"Force: {args.force}")
    print()

    if args.force:
        print("⚠️  WARNING: Force mode enabled - local changes will be overwritten!")
        response = input("Continue? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            return 0

    # Execute pull
    results = manager.pull_prompts(names=names, label=args.label, force=args.force)

    # Print results
    print_section("Results")
    success_count = sum(1 for success in results.values() if success)
    failed_count = len(results) - success_count

    for name, success in results.items():
        icon = "✅" if success else "❌"
        status = "SUCCESS" if success else "FAILED"
        print(f"{icon} {name:40s} - {status}")

    print()
    print(f"Total: {len(results)} prompts")
    print(f"✅ Success: {success_count}")
    print(f"❌ Failed: {failed_count}")

    if failed_count == 0:
        print("\n🎉 All prompts pulled successfully!")

    return 0 if failed_count == 0 else 1


def cmd_push(args):
    """Push prompts from local files to Langfuse"""
    print_header("Push Prompts to Langfuse")

    if not LANGFUSE_ENABLED:
        print("❌ Error: Langfuse is not enabled. Set LANGFUSE_ENABLED=true in .env")
        return 1

    manager = PromptSyncManager()
    names = parse_names(args.names)
    labels = parse_labels(args.labels)

    if names:
        print(f"Pushing prompts: {', '.join(names)}")
    else:
        print("Pushing all prompts")

    print(f"Labels: {', '.join(labels)}")
    print(f"Force: {args.force}")
    print()

    if args.force:
        print("⚠️  WARNING: Force mode enabled - remote changes will be overwritten!")
        response = input("Continue? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            return 0

    # Execute push
    results = manager.push_prompts(names=names, force=args.force, labels=labels)

    # Print results
    print_section("Results")
    success_count = sum(1 for success in results.values() if success)
    failed_count = len(results) - success_count

    for name, success in results.items():
        icon = "✅" if success else "❌"
        status = "SUCCESS" if success else "FAILED"
        print(f"{icon} {name:40s} - {status}")

    print()
    print(f"Total: {len(results)} prompts")
    print(f"✅ Success: {success_count}")
    print(f"❌ Failed: {failed_count}")

    if failed_count == 0:
        print("\n🎉 All prompts pushed successfully!")

    return 0 if failed_count == 0 else 1


def cmd_status(args):
    """Check sync status of prompts"""
    print_header("Prompt Sync Status")

    manager = PromptSyncManager()
    names = parse_names(args.names)

    if names:
        print(f"Checking status for: {', '.join(names)}\n")
    else:
        print("Checking status for all prompts\n")

    # Get status
    status_map = manager.check_sync_status(names=names)

    # Group by status
    status_groups = {}
    for name, status in status_map.items():
        if status not in status_groups:
            status_groups[status] = []
        status_groups[status].append(name)

    # Print grouped results
    for status_type in [
        SyncStatus.SYNCED,
        SyncStatus.MODIFIED_LOCAL,
        SyncStatus.MODIFIED_REMOTE,
        SyncStatus.CONFLICT,
        SyncStatus.NEW_LOCAL,
        SyncStatus.NEW_REMOTE,
        SyncStatus.NOT_FOUND
    ]:
        if status_type in status_groups:
            prompts = status_groups[status_type]
            icon = STATUS_ICONS[status_type]
            description = STATUS_DESCRIPTIONS[status_type]
            print(f"\n{icon} {description} ({len(prompts)})")
            for name in prompts:
                local_file = LANGFUSE_NAME_TO_FILE.get(name, "N/A")
                print(f"   • {name:40s} ({local_file})")

    # Summary
    print_section("Summary")
    total = len(status_map)
    synced = len(status_groups.get(SyncStatus.SYNCED, []))
    conflicts = len(status_groups.get(SyncStatus.CONFLICT, []))
    modified = len(status_groups.get(SyncStatus.MODIFIED_LOCAL, [])) + \
               len(status_groups.get(SyncStatus.MODIFIED_REMOTE, []))

    print(f"Total prompts: {total}")
    print(f"✅ Synced: {synced}")
    print(f"📝 Modified: {modified}")
    print(f"⚠️  Conflicts: {conflicts}")

    if conflicts > 0:
        print("\n⚠️  Conflicts detected! Use 'resolve' command to fix them:")
        for name in status_groups.get(SyncStatus.CONFLICT, []):
            print(f"   python scripts/sync_prompts.py resolve {name} --strategy <local|remote>")

    return 0


def cmd_resolve(args):
    """Resolve conflict for a prompt"""
    print_header(f"Resolve Conflict: {args.name}")

    if not LANGFUSE_ENABLED:
        print("❌ Error: Langfuse is not enabled. Set LANGFUSE_ENABLED=true in .env")
        return 1

    manager = PromptSyncManager()

    # Check if prompt exists
    if args.name not in LANGFUSE_NAME_TO_FILE:
        print(f"❌ Error: Unknown prompt name '{args.name}'")
        print(f"\nAvailable prompts: {', '.join(LANGFUSE_NAME_TO_FILE.keys())}")
        return 1

    # Verify it's actually a conflict
    status_map = manager.check_sync_status([args.name])
    current_status = status_map.get(args.name)

    print(f"Current status: {STATUS_ICONS.get(current_status, '❓')} {STATUS_DESCRIPTIONS.get(current_status, 'Unknown')}")
    print(f"Resolution strategy: {args.strategy}")
    print()

    if current_status != SyncStatus.CONFLICT:
        print(f"⚠️  Warning: '{args.name}' is not in conflict state.")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            return 0

    # Confirm resolution
    if args.strategy == "local":
        print("This will push your local version to Langfuse, overwriting the remote version.")
    elif args.strategy == "remote":
        print("This will pull the remote version from Langfuse, overwriting your local version.")
    else:
        print(f"❌ Error: Invalid strategy '{args.strategy}'. Must be 'local' or 'remote'")
        return 1

    response = input("Continue? (y/N): ")
    if response.lower() != 'y':
        print("Aborted.")
        return 0

    # Resolve conflict
    success = manager.resolve_conflict(args.name, strategy=args.strategy)

    if success:
        print(f"\n✅ Conflict resolved for '{args.name}' using '{args.strategy}' strategy")
        return 0
    else:
        print(f"\n❌ Failed to resolve conflict for '{args.name}'")
        return 1


def cmd_init(args):
    """Initialize metadata file"""
    print_header("Initialize Prompt Metadata")

    manager = PromptSyncManager()

    if manager.metadata_file.exists() and not args.force:
        print(f"⚠️  Metadata file already exists: {manager.metadata_file}")
        response = input("Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            return 0

    success = manager.initialize_metadata()

    if success:
        print("\n🎉 Metadata initialized successfully!")
        return 0
    else:
        print("\n❌ Failed to initialize metadata")
        return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Langfuse Prompt Synchronization CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    subparsers.required = True

    # Pull command
    pull_parser = subparsers.add_parser("pull", help="Pull prompts from Langfuse to local")
    pull_parser.add_argument(
        "--names",
        type=str,
        help="Comma-separated list of prompt names to pull (e.g., 'reasoning-agent,validation-agent')"
    )
    pull_parser.add_argument(
        "--label",
        type=str,
        default="production",
        help="Label to fetch from Langfuse (default: production)"
    )
    pull_parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite local changes"
    )
    pull_parser.set_defaults(func=cmd_pull)

    # Push command
    push_parser = subparsers.add_parser("push", help="Push prompts from local to Langfuse")
    push_parser.add_argument(
        "--names",
        type=str,
        help="Comma-separated list of prompt names to push"
    )
    push_parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite remote changes"
    )
    push_parser.add_argument(
        "--labels",
        type=str,
        default="production",
        help="Comma-separated labels to apply (default: production)"
    )
    push_parser.set_defaults(func=cmd_push)

    # Status command
    status_parser = subparsers.add_parser("status", help="Check sync status")
    status_parser.add_argument(
        "--names",
        type=str,
        help="Comma-separated list of prompt names to check"
    )
    status_parser.set_defaults(func=cmd_status)

    # Resolve command
    resolve_parser = subparsers.add_parser("resolve", help="Resolve conflict")
    resolve_parser.add_argument(
        "name",
        type=str,
        help="Prompt name to resolve"
    )
    resolve_parser.add_argument(
        "--strategy",
        type=str,
        required=True,
        choices=["local", "remote"],
        help="Resolution strategy: 'local' (keep local) or 'remote' (keep remote)"
    )
    resolve_parser.set_defaults(func=cmd_resolve)

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize metadata file")
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite existing metadata"
    )
    init_parser.set_defaults(func=cmd_init)

    # Parse args and execute command
    args = parser.parse_args()

    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        return 130
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
