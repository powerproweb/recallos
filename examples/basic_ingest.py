#!/usr/bin/env python3
"""Example: ingest a project folder into the Data Vault."""

import sys

project_dir = sys.argv[1] if len(sys.argv) > 1 else "~/projects/my_app"
print("Step 1: Initialize nodes from folder structure")
print(f"  recallos init {project_dir}")
print("\nStep 2: Ingest everything")
print(f"  recallos ingest {project_dir}")
print("\nStep 3: Query")
print("  recallos query 'why did we choose this approach'")
