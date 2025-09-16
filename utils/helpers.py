import os
from pathlib import Path
from langchain_core.messages import convert_to_messages


def pretty_print_message(message, indent=False):
    pretty_message = message.pretty_repr(html=True)
    if not indent:
        print(pretty_message)
        return

    indented = "\n".join("\t" + c for c in pretty_message.split("\n"))
    print(indented)


def pretty_print_messages(update, last_message=False):
    is_subgraph = False
    if isinstance(update, tuple):
        ns, update = update
        # skip parent graph updates in the printouts
        if len(ns) == 0:
            return

        graph_id = ns[-1].split(":")[0]
        print(f"Update from subgraph {graph_id}:")
        print("\n")
        is_subgraph = True

    for node_name, node_update in update.items():
        update_label = f"Update from node {node_name}:"
        if is_subgraph:
            update_label = "\t" + update_label

        print(update_label)
        print("\n")

        messages = convert_to_messages(node_update["messages"])
        if last_message:
            messages = messages[-1:]

        for m in messages:
            pretty_print_message(m, indent=is_subgraph)
        print("\n")


def get_project_root():
    """Get the project root directory"""
    return Path(__file__).parent.parent


def get_data_path(filename=""):
    """Get path to data directory or specific file in data directory"""
    return get_project_root() / "data" / filename


def get_prompts_path(filename=""):
    """Get path to prompts directory or specific file in prompts directory"""
    return get_project_root() / "prompts" / filename


def get_sessions_path(session_id=""):
    """Get path to sessions directory or specific session folder"""
    sessions_dir = get_project_root() / "sessions"
    if session_id:
        return sessions_dir / session_id
    return sessions_dir


def ensure_directory_exists(path):
    """Ensure a directory exists, create if it doesn't"""
    Path(path).mkdir(parents=True, exist_ok=True)
    return path