#!/usr/bin/env python3
"""
Migration script to upload existing prompts from local files to Langfuse

Usage:
    python scripts/migrate_prompts_to_langfuse.py [--dry-run] [--update-metadata]

Options:
    --dry-run: Show what would be migrated without actually uploading
    --update-metadata: Update metadata file after migration
"""
import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path to import project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.langfuse_config import create_prompt_in_langfuse, get_langfuse_client
from utils.prompt_sync import PromptSyncManager
from config.settings import OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_MAX_TOKENS


# Mapping of local file names to Langfuse prompt names (kebab-case)
PROMPT_MAPPING = {
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


def migrate_prompts(dry_run: bool = False, update_metadata: bool = False):
    """
    Migrate all prompts from local files to Langfuse

    Args:
        dry_run: If True, only print what would be migrated without uploading
        update_metadata: If True, update metadata file after migration
    """
    print("=" * 80)
    print("Langfuse Prompt Migration Script")
    print("=" * 80)
    print()

    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made to Langfuse")
        print()

    if update_metadata:
        print("📝 Metadata update enabled")
        print()

    # Check Langfuse connection
    if not dry_run:
        client = get_langfuse_client()
        if not client:
            print("❌ Error: Cannot connect to Langfuse. Please check your configuration.")
            print("   - Ensure LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are set in .env")
            print("   - Ensure LANGFUSE_ENABLED=true in .env")
            return False

        print("✅ Successfully connected to Langfuse")
        print()

    # Find prompts directory
    prompts_dir = Path("prompts")
    if not prompts_dir.exists():
        print(f"❌ Error: Prompts directory not found at {prompts_dir.absolute()}")
        return False

    print(f"📁 Reading prompts from: {prompts_dir.absolute()}")
    print()

    # Migrate each prompt
    success_count = 0
    failed_count = 0
    results = []

    for file_name, langfuse_name in PROMPT_MAPPING.items():
        file_path = prompts_dir / file_name

        if not file_path.exists():
            print(f"⚠️  WARNING: File not found: {file_name}")
            failed_count += 1
            results.append({
                "name": langfuse_name,
                "file": file_name,
                "status": "SKIPPED",
                "reason": "File not found"
            })
            continue

        # Read prompt content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                prompt_content = f.read()
        except Exception as e:
            print(f"❌ ERROR reading {file_name}: {e}")
            failed_count += 1
            results.append({
                "name": langfuse_name,
                "file": file_name,
                "status": "FAILED",
                "reason": f"Read error: {e}"
            })
            continue

        # Prepare config based on agent type
        config = {
            "model": OPENAI_MODEL,
            "temperature": OPENAI_TEMPERATURE,
            "max_tokens": OPENAI_MAX_TOKENS
        }

        # Add response_format for specific agents
        if "reasoning" in langfuse_name:
            config["response_format"] = "ReasoningOutput"
        elif "validation" in langfuse_name:
            config["response_format"] = "ValidationOutput"
        elif "report" in langfuse_name:
            config["response_format"] = "ReportOutput"
        elif "info-retriever" in langfuse_name:
            config["response_format"] = "InfoRetrieverOutput"

        labels = ["production", "v1.0", "migrated"]

        if dry_run:
            print(f"📝 Would migrate: {file_name} → {langfuse_name}")
            print(f"   Labels: {labels}")
            print(f"   Config: {config}")
            print(f"   Content length: {len(prompt_content)} chars")
            print()
            success_count += 1
            results.append({
                "name": langfuse_name,
                "file": file_name,
                "status": "DRY_RUN",
                "chars": len(prompt_content)
            })
        else:
            # Actually create the prompt in Langfuse
            print(f"⬆️  Uploading: {file_name} → {langfuse_name}... ", end="")
            success = create_prompt_in_langfuse(
                name=langfuse_name,
                prompt=prompt_content,
                config=config,
                labels=labels
            )

            if success:
                print("✅ SUCCESS")
                success_count += 1
                results.append({
                    "name": langfuse_name,
                    "file": file_name,
                    "status": "SUCCESS",
                    "chars": len(prompt_content)
                })
            else:
                print("❌ FAILED")
                failed_count += 1
                results.append({
                    "name": langfuse_name,
                    "file": file_name,
                    "status": "FAILED",
                    "reason": "Upload failed"
                })

    # Print summary
    print()
    print("=" * 80)
    print("Migration Summary")
    print("=" * 80)
    print()

    for result in results:
        status_icon = {
            "SUCCESS": "✅",
            "FAILED": "❌",
            "SKIPPED": "⚠️ ",
            "DRY_RUN": "📝"
        }.get(result["status"], "❓")

        print(f"{status_icon} {result['name']:40s} ({result['file']:35s}) - {result['status']}")
        if "reason" in result:
            print(f"   Reason: {result['reason']}")

    print()
    print(f"Total prompts processed: {len(results)}")
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {failed_count}")
    print()

    if not dry_run and success_count > 0:
        print("🎉 Migration completed!")
        print()

        # Update metadata if requested
        if update_metadata:
            print("📝 Updating metadata file...")
            try:
                sync_manager = PromptSyncManager()
                sync_manager.initialize_metadata()
                print("✅ Metadata updated successfully")
            except Exception as e:
                print(f"⚠️  Warning: Failed to update metadata: {e}")

        print()
        print("Next steps:")
        print("1. Verify prompts in Langfuse UI")
        print("2. Test the application with LANGFUSE_PROMPT_MANAGEMENT_ENABLED=true")
        print("3. Monitor logs to ensure prompts are being fetched correctly")
        if update_metadata:
            print("4. Check prompts/.prompt_metadata.json for sync tracking")
        print()

    return failed_count == 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Migrate prompts from local files to Langfuse",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without actually uploading"
    )
    parser.add_argument(
        "--update-metadata",
        action="store_true",
        help="Update metadata file after migration"
    )

    args = parser.parse_args()

    success = migrate_prompts(dry_run=args.dry_run, update_metadata=args.update_metadata)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
