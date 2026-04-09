#!/usr/bin/env python3
"""
room_detector_local.py â€” Local setup, no API required.

Two ways to define nodes without calling any AI:
  1. Auto-detect from folder structure (zero config)
  2. Define manually in recallos.yaml

No internet. No API key. Your files stay on your machine.
"""

import os
import sys
import yaml
from pathlib import Path
from collections import defaultdict

# Common node patterns â€” detected from folder names and filenames
# Format: {folder_keyword: node_name}
FOLDER_NODE_MAP = {
    "frontend": "frontend",
    "front-end": "frontend",
    "front_end": "frontend",
    "client": "frontend",
    "ui": "frontend",
    "views": "frontend",
    "components": "frontend",
    "pages": "frontend",
    "backend": "backend",
    "back-end": "backend",
    "back_end": "backend",
    "server": "backend",
    "api": "backend",
    "routes": "backend",
    "services": "backend",
    "controllers": "backend",
    "models": "backend",
    "database": "backend",
    "db": "backend",
    "docs": "documentation",
    "doc": "documentation",
    "documentation": "documentation",
    "wiki": "documentation",
    "readme": "documentation",
    "notes": "documentation",
    "design": "design",
    "designs": "design",
    "mockups": "design",
    "wireframes": "design",
    "assets": "design",
    "storyboard": "design",
    "costs": "costs",
    "cost": "costs",
    "budget": "costs",
    "finance": "costs",
    "financial": "costs",
    "pricing": "costs",
    "invoices": "costs",
    "accounting": "costs",
    "meetings": "meetings",
    "meeting": "meetings",
    "calls": "meetings",
    "meeting_notes": "meetings",
    "standup": "meetings",
    "minutes": "meetings",
    "team": "team",
    "staff": "team",
    "hr": "team",
    "hiring": "team",
    "employees": "team",
    "people": "team",
    "research": "research",
    "references": "research",
    "reading": "research",
    "papers": "research",
    "planning": "planning",
    "roadmap": "planning",
    "strategy": "planning",
    "specs": "planning",
    "requirements": "planning",
    "tests": "testing",
    "test": "testing",
    "testing": "testing",
    "qa": "testing",
    "scripts": "scripts",
    "tools": "scripts",
    "utils": "scripts",
    "config": "configuration",
    "configs": "configuration",
    "settings": "configuration",
    "infrastructure": "configuration",
    "infra": "configuration",
    "deploy": "configuration",
}


def detect_nodes_from_folders(project_dir: str) -> list:
    """
    Walk the project folder structure.
    Find top-level subdirectories that match known node patterns.
    Returns list of node dicts.
    """
    project_path = Path(project_dir).expanduser().resolve()
    found_nodes = {}

    SKIP_DIRS = {
        ".git",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        "env",
        "dist",
        "build",
        ".next",
        "coverage",
    }

    # Check top-level directories first (most reliable signal)
    for item in project_path.iterdir():
        if item.is_dir() and item.name not in SKIP_DIRS:
            name_lower = item.name.lower().replace("-", "_")
            if name_lower in FOLDER_NODE_MAP:
                node_name = FOLDER_NODE_MAP[name_lower]
                if node_name not in found_nodes:
                    found_nodes[node_name] = item.name
            # Also check if folder name IS a good node name directly
            elif len(item.name) > 2 and item.name[0].isalpha():
                clean = item.name.lower().replace("-", "_").replace(" ", "_")
                if clean not in found_nodes:
                    found_nodes[clean] = item.name

    # Walk one level deeper for nested patterns
    for item in project_path.iterdir():
        if item.is_dir() and item.name not in SKIP_DIRS:
            for subitem in item.iterdir():
                if subitem.is_dir() and subitem.name not in SKIP_DIRS:
                    name_lower = subitem.name.lower().replace("-", "_")
                    if name_lower in FOLDER_NODE_MAP:
                        node_name = FOLDER_NODE_MAP[name_lower]
                        if node_name not in found_nodes:
                            found_nodes[node_name] = subitem.name

    # Build node list
    nodes = []
    for node_name, original in found_nodes.items():
        nodes.append(
            {
                "name": node_name,
                "description": f"Files from {original}/",
                "keywords": [node_name, original.lower()],
            }
        )

    # Always add "general" as fallback
    if not any(n["name"] == "general" for n in nodes):
        nodes.append(
            {
                "name": "general",
                "description": "Files that don't fit other nodes",
                "keywords": [],
            }
        )

    return nodes


def detect_nodes_from_files(project_dir: str) -> list:
    """
    Fallback: if folder structure gives no signal,
    detect nodes from recurring filename patterns.
    """
    project_path = Path(project_dir).expanduser().resolve()
    keyword_counts = defaultdict(int)

    SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}

    for root, dirs, filenames in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for filename in filenames:
            name_lower = filename.lower().replace("-", "_").replace(" ", "_")
            for keyword, node_name in FOLDER_NODE_MAP.items():
                if keyword in name_lower:
                    keyword_counts[node_name] += 1

    # return nodes that appear more than twice
    nodes = []
    for node_name, count in sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True):
        if count >= 2:
            nodes.append(
                {
                    "name": node_name,
                    "description": f"Files related to {node_name}",
                    "keywords": [node_name],
                }
            )
        if len(nodes) >= 6:
            break

    if not nodes:
        nodes = [{"name": "general", "description": "All project files", "keywords": []}]

    return nodes


def print_proposed_structure(project_name: str, nodes: list, total_files: int, source: str):
    print(f"\n{'=' * 55}")
    print("  RecallOS Init â€” Local setup")
    print(f"{'=' * 55}")
    print(f"\n  DOMAIN: {project_name}")
    print(f"  ({total_files} files found, nodes detected from {source})\n")
    for node in nodes:
        print(f"    NODE:   {node['name']}")
        print(f"          {node['description']}")
    print(f"\n{'â”€' * 55}")


def get_user_approval(nodes: list) -> list:
    """Same approval flow as AI version."""
    print("  Review the proposed nodes above.")
    print("  Options:")
    print("    [enter]  Accept all nodes")
    print("    [edit]   Remove or rename nodes")
    print("    [add]    Add a node manually")
    print()

    choice = input("  Your choice [enter/edit/add]: ").strip().lower()

    if choice in ("", "y", "yes"):
        return nodes

    if choice == "edit":
        print("\n  Current nodes:")
        for i, node in enumerate(nodes):
            print(f"    {i + 1}. {node['name']} – {node['description']}")
        remove = input("\n  Node numbers to REMOVE (comma-separated, or enter to skip): ").strip()
        if remove:
            to_remove = {int(x.strip()) - 1 for x in remove.split(",") if x.strip().isdigit()}
            nodes = [n for i, n in enumerate(nodes) if i not in to_remove]

    if choice == "add" or input("\n  Add any missing nodes? [y/N]: ").strip().lower() == "y":
        while True:
            new_name = (
                input("  New node name (or enter to stop): ").strip().lower().replace(" ", "_")
            )
            if not new_name:
                break
            new_desc = input(f"  Description for '{new_name}': ").strip()
            nodes.append({"name": new_name, "description": new_desc, "keywords": [new_name]})
            print(f"  Added: {new_name}")

    return nodes


def save_config(project_dir: str, project_name: str, nodes: list):
    config = {
        "domain": project_name,
        "nodes": [{"name": n["name"], "description": n["description"]} for n in nodes],
    }
    config_path = Path(project_dir).expanduser().resolve() / "recallos.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"\n  Config saved: {config_path}")
    print("\n  Next step:")
    print(f"    recallos ingest {project_dir}")
    print(f"\n{'=' * 55}\n")


def detect_nodes_local(project_dir: str):
    """Main entry point for local setup."""
    project_path = Path(project_dir).expanduser().resolve()
    project_name = project_path.name.lower().replace(" ", "_").replace("-", "_")

    if not project_path.exists():
        print(f"ERROR: Directory not found: {project_dir}")
        sys.exit(1)

    # Count files
    from .ingest_engine import scan_project

    files = scan_project(project_dir)

    # Try folder structure first
    nodes = detect_nodes_from_folders(project_dir)
    source = "folder structure"

    # If only "general" found, try filename patterns
    if len(nodes) <= 1:
        nodes = detect_nodes_from_files(project_dir)
        source = "filename patterns"

    # If still nothing, just use general
    if not nodes:
        nodes = [{"name": "general", "description": "All project files", "keywords": []}]
        source = "fallback (flat project)"

    print_proposed_structure(project_name, nodes, len(files), source)
    approved_nodes = get_user_approval(nodes)
    save_config(project_dir, project_name, approved_nodes)
