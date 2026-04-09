#!/usr/bin/env python3
"""Example: ingest Claude Code / ChatGPT conversations into the Data Vault."""

print("Ingest Claude Code sessions:")
print("  recallos ingest ~/claude-sessions/ --mode convos --domain my_project")
print()
print("Ingest ChatGPT exports:")
print("  recallos ingest ~/chatgpt-exports/ --mode convos")
print()
print("Use general extractor for richer extraction:")
print("  recallos ingest ~/chats/ --mode convos --extract general")
